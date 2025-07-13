# app/ExchangeFetcher/fetcher.py

import argparse
import requests
import select
import sys
import time
import json
import asyncio
import websockets
from datetime import datetime, timezone
from config import BINANCE_API_BASE_URL, DEFAULT_SYMBOL
from DatabaseOperator.pg_operator import Session, engine, init_db, insert_price, insert_kline
from DataProcessingCalculator.DataModificationModule import parse_kline

def fetch_price(SYMBOL,Price):
    """
    从 Binance API 获取最新价格并存储到数据库
    参数:Price 表对象
    返回值:存储的价格值
    """
    try:
        symbol = SYMBOL  # 动态获取当前交易对
        url = f'{BINANCE_API_BASE_URL}ticker/price?symbol={symbol}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = float(data['price'])
        session = Session()
        custom_id = insert_price(session, Price, symbol, price, datetime.now(timezone.utc))
        session.close()
        print(f"[Fetcher] Stored price: {price}, id: {custom_id}")
        return price
    except Exception as e:
        print(f"[Fetcher] Error: {e}")
        return None


# K Line
# 需要(symbol, interval, dbr=False, session=None, table=None,startTime=None, endTime=None, limit=100)
def get_kline(symbol, interval, dbr, session, table=None,
              startTime=None, endTime=None, limit=100):
    """
    获取 Binance K 线数据，并可选择写入数据库。

    参数：
        symbol     - 币种对（如 "BTCUSDT"）
        interval   - K线周期（如 "1h", "1d"）
        dbr        - 是否写入数据库（True 则执行 insert_kline）
        session    - SQLAlchemy 数据库 session（必填于 dbr=True）
        table      - SQLAlchemy 的表对象（dbr=True时可选，如果为None会自动创建）
        startTime  - 开始时间（Unix 毫秒）
        endTime    - 结束时间（Unix 毫秒）
        limit      - 获取数量，最大 1000

    返回：
        kline_data - 原始 K 线数据列表
    """
    url = f'{BINANCE_API_BASE_URL}klines'
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "limit": limit
    }
    if startTime:
        params["startTime"] = startTime
    if endTime:
        params["endTime"] = endTime

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        kline_data = response.json()

        if dbr:
            if session is None:
                raise ValueError("写入数据库时 session 参数不能为空")
                
            # 如果表为None，使用create_kline_table_if_not_exists创建表
            if table is None:
                from app.DatabaseOperator.pg_operator import create_kline_table_if_not_exists, engine
                table = create_kline_table_if_not_exists(engine, symbol.upper())
                
            for raw_k in kline_data:
                parsed_kline = parse_kline(raw_k)

                # 跳过未来数据
                if parsed_kline['open_time'] > int(datetime.now(timezone.utc).timestamp() * 1000):
                    continue

                insert_kline(session, table, symbol.upper(), parsed_kline)

        return [parse_kline(k) for k in kline_data]

    except requests.RequestException as e:
        print(f"[错误] 请求失败: {e}")
        return []

# WebSocket K Line - WebSocket版本的get_kline
async def get_kline_websocket(symbol, interval, dbr=False, session=None, table=None, 
                             callback=None, max_klines=None, auto_reconnect=True):
    """
    通过WebSocket获取 Binance K 线数据，并可选择写入数据库。
    这是get_kline函数的WebSocket实时版本。

    参数：
        symbol          - 币种对（如 "BTCUSDT"）
        interval        - K线周期（如 "1m", "5m", "1h", "1d"）
        dbr             - 是否写入数据库（True 则执行 insert_kline）
        session         - SQLAlchemy 数据库 session（必填于 dbr=True）
        table           - SQLAlchemy 的表对象（dbr=True时可选，如果为None会自动创建）
        callback        - 回调函数，接收每个K线数据
        max_klines      - 最大接收K线数量（None表示无限制）
        auto_reconnect  - 是否自动重连（默认True）

    返回：
        kline_data_list - 接收到的解析后K线数据列表
    """
    # WebSocket URL配置
    ws_url = "wss://stream.binance.com:9443"
    stream_name = f"{symbol.lower()}@kline_{interval}"
    ws_endpoint = f"{ws_url}/ws/{stream_name}"
    
    kline_data_list = []  # 存储接收到的K线数据
    kline_count = 0
    reconnect_count = 0
    max_reconnect_attempts = 5
    
    # 数据库表初始化
    if dbr:
        if session is None:
            raise ValueError("写入数据库时 session 参数不能为空")
        
        if table is None:
            from DatabaseOperator.pg_operator import create_kline_table_if_not_exists
            table = create_kline_table_if_not_exists(engine, symbol.upper())
    
    print(f"[WebSocket] 连接到 {symbol} {interval} K线流...")
    
    while reconnect_count <= max_reconnect_attempts:
        try:
            async with websockets.connect(
                ws_endpoint, 
                ping_interval=20, 
                ping_timeout=10,
                close_timeout=10
            ) as websocket:
                print(f"[WebSocket] 成功连接 {symbol} {interval} K线数据流")
                reconnect_count = 0  # 重置重连计数
                
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        # 检查是否为K线数据
                        if 'k' in data:
                            kline_raw = data['k']
                            
                            # 转换为与REST API相同的格式 [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, ...]
                            kline_array = [
                                kline_raw['t'],      # 开盘时间
                                kline_raw['o'],      # 开盘价
                                kline_raw['h'],      # 最高价
                                kline_raw['l'],      # 最低价
                                kline_raw['c'],      # 收盘价
                                kline_raw['v'],      # 成交量
                                kline_raw['T'],      # 收盘时间
                                kline_raw['q'],      # 成交额
                                kline_raw['n'],      # 成交数量
                                kline_raw['V'],      # 主动买入成交量
                                kline_raw['Q'],      # 主动买入成交额
                                "0"                  # 忽略字段
                            ]
                            
                            # 使用现有的parse_kline函数解析
                            parsed_kline = parse_kline(kline_array)
                            
                            # 添加WebSocket特有字段
                            parsed_kline['is_closed'] = kline_raw['x']  # K线是否完结
                            parsed_kline['symbol'] = kline_raw['s']     # 交易对
                            parsed_kline['interval'] = kline_raw['i']   # 间隔
                            
                            # 跳过未来数据（与REST版本保持一致）
                            if parsed_kline['open_time'] > int(datetime.now(timezone.utc).timestamp() * 1000):
                                continue
                            
                            # 添加到结果列表
                            kline_data_list.append(parsed_kline)
                            kline_count += 1
                            
                            # 调用回调函数
                            if callback:
                                callback(parsed_kline)
                            
                            # 数据库写入（仅当K线完结时，保持与REST版本一致的行为）
                            if dbr and parsed_kline['is_closed'] and session is not None:
                                try:
                                    insert_kline(session, table, symbol.upper(), parsed_kline)
                                    session.commit()
                                    print(f"[WebSocket] 已保存完结K线到数据库: {symbol} {interval}")
                                except Exception as db_error:
                                    print(f"[WebSocket] 数据库写入错误: {db_error}")
                                    session.rollback()
                            
                            # 检查是否达到最大K线数量
                            if max_klines and kline_count >= max_klines:
                                print(f"[WebSocket] 已接收 {max_klines} 个K线，停止接收")
                                return kline_data_list
                        
                    except json.JSONDecodeError as e:
                        print(f"[WebSocket] JSON解析错误: {e}")
                        continue
                    except Exception as e:
                        print(f"[WebSocket] 数据处理错误: {e}")
                        continue
                        
        except websockets.exceptions.ConnectionClosed as e:
            print(f"[WebSocket] 连接关闭: {e}")
            if auto_reconnect and reconnect_count < max_reconnect_attempts:
                reconnect_count += 1
                wait_time = min(2 ** reconnect_count, 30)  # 指数退避
                print(f"[WebSocket] {wait_time}秒后尝试重连 (第{reconnect_count}次)")
                await asyncio.sleep(wait_time)
            else:
                print(f"[WebSocket] 停止重连")
                break
                
        except Exception as e:
            print(f"[WebSocket] 连接错误: {e}")
            if auto_reconnect and reconnect_count < max_reconnect_attempts:
                reconnect_count += 1
                wait_time = min(2 ** reconnect_count, 30)
                print(f"[WebSocket] {wait_time}秒后尝试重连 (第{reconnect_count}次)")
                await asyncio.sleep(wait_time)
            else:
                print(f"[WebSocket] 停止重连")
                break
    
    print(f"[WebSocket] 总共接收了 {len(kline_data_list)} 个K线数据")
    return kline_data_list


def start_kline_websocket_sync(symbol, interval, dbr=False, session=None, table=None, 
                              callback=None, max_klines=None):
    """
    get_kline_websocket的同步包装函数，方便在非异步环境中使用
    
    参数与get_kline_websocket相同
    
    返回：
        kline_data_list - 接收到的解析后K线数据列表
    """
    return asyncio.run(get_kline_websocket(
        symbol=symbol,
        interval=interval,
        dbr=dbr,
        session=session,
        table=table,
        callback=callback,
        max_klines=max_klines
    ))