# app/ExchangeFetcher/fetcher.py

import argparse
import requests
import select
import sys
import time
import logging
import json
import asyncio
import websockets
from datetime import datetime, timezone
from config import BINANCE_API_BASE_URL, DEFAULT_SYMBOL

from config import quick_setup, get_logger
quick_setup()
logger = get_logger()
logger.info("开始使用新的日志配置！")

from DatabaseOperator.pg_operator import Session, engine, init_db, insert_price, insert_kline
from DataProcessingCalculator.DataModificationModule import parse_kline

def fetch_price(SYMBOL, Price, session=None):
    """
    从 Binance API 获取最新价格并存储到数据库
    参数:
        SYMBOL - 交易对符号
        Price - 表对象
        session - 数据库会话（可选，如果为None则不存储到数据库）
    返回值:存储的价格值
    """
    try:
        symbol = SYMBOL  # 动态获取当前交易对
        url = f'{BINANCE_API_BASE_URL}ticker/price?symbol={symbol}'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = float(data['price'])
        
        # 只有提供session时才存储到数据库
        if session is not None and Price is not None:
            custom_id = insert_price(session, Price, symbol, price, datetime.now(timezone.utc))
            logger.debug(f"Stored price: {price}, id: {custom_id}")
        
        return price
    except Exception as e:
        logger.error(f"Failed to fetch price for {SYMBOL}: {e}")
        return None


# K Line
# 需要(symbol, interval, dbr=False, session=None, table=None,startTime=None, endTime=None, limit=100)
def get_kline(symbol, interval, dbr, session, table=None,
              startTime=None, endTime=None, limit=100, auto_commit=False):
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
        auto_commit - 是否自动提交每次写入（默认False）

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
                from DatabaseOperator.pg_operator import create_kline_table_if_not_exists
                table = create_kline_table_if_not_exists(engine, symbol.upper())
                
            for raw_k in kline_data:
                parsed_kline = parse_kline(raw_k)

                # 跳过未来数据
                if parsed_kline['open_time'] > int(datetime.now(timezone.utc).timestamp() * 1000):
                    continue

                insert_kline(session, table, symbol.upper(), parsed_kline)
                
                # 自动提交选项：立即提交使数据对其他连接可见
                if auto_commit:
                    session.commit()

        return [parse_kline(k) for k in kline_data]

    except requests.RequestException as e:
        logger.error(f"Failed to fetch klines for {symbol} {interval}: {e}")
        return []

# WebSocket K Line - WebSocket版本的get_kline
async def get_kline_websocket(symbol, interval, dbr=False, session=None, table=None, 
                             callback=None, max_klines=None, auto_reconnect=True, auto_commit=False):
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
        auto_commit     - 是否自动提交每次写入（默认False，推荐实时场景使用True）

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
    
    logger.info(f"Starting WebSocket connection for {symbol} {interval} klines")
    
    while reconnect_count <= max_reconnect_attempts:
        try:
            async with websockets.connect(
                ws_endpoint, 
                ping_interval=20, 
                ping_timeout=10,
                close_timeout=10
            ) as websocket:
                logger.info(f"Successfully connected to {symbol} {interval} kline stream")
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
                            
                            # 数据库写入（为了测试，暂时允许未完结的K线也入库）(哪有完结的K线，不然实时数据都没法存了)
                            if dbr and session is not None:
                                try:
                                    insert_kline(session, table, symbol.upper(), parsed_kline)
                                    
                                    # 自动提交选项：立即提交使数据对其他连接可见
                                    if auto_commit:
                                        session.commit()
                                        
                                except Exception as db_error:
                                    logger.error(f"Database write error for {symbol}: {db_error}")
                                    if auto_commit:
                                        session.rollback()  # 自动提交模式下需要回滚
                            
                            # 检查是否达到最大K线数量
                            if max_klines and kline_count >= max_klines:
                                logger.info(f"Received {max_klines} klines for {symbol}, stopping")
                                return kline_data_list
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON decode error: {e}")
                        continue
                    except Exception as e:
                        logger.error(f"Data processing error: {e}")
                        continue
                        
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"WebSocket connection closed: {e}")
            if auto_reconnect and reconnect_count < max_reconnect_attempts:
                reconnect_count += 1
                wait_time = min(2 ** reconnect_count, 30)  # 指数退避
                logger.info(f"Attempting reconnection #{reconnect_count} in {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                logger.info("Stopping reconnection attempts")
                break
                
        except Exception as e:
            logger.error(f"WebSocket connection error: {e}")
            if auto_reconnect and reconnect_count < max_reconnect_attempts:
                reconnect_count += 1
                wait_time = min(2 ** reconnect_count, 30)
                logger.info(f"Attempting reconnection #{reconnect_count} in {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                logger.info("Stopping reconnection attempts")
                break
    
    logger.info(f"WebSocket session completed: received {len(kline_data_list)} klines for {symbol}")
    return kline_data_list


def start_kline_websocket_sync(symbol, interval, dbr=False, session=None, table=None, 
                              callback=None, max_klines=None, auto_commit=False):
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
        max_klines=max_klines,
        auto_commit=auto_commit
    ))


# WebSocket K线使用示例
async def example_websocket_kline_usage():
    """
    WebSocket K线数据获取的示例用法
    """
    def kline_callback(kline_data):
        """处理接收到的K线数据的回调函数"""
        logger.info(f"Received kline: {kline_data['symbol']} {kline_data['interval']} - Close: {kline_data['close']}, Volume: {kline_data['volume']}, Closed: {kline_data['is_closed']}")
    
    # 示例1: 只接收数据不入库
    logger.info("Example 1: Getting BTC 1m klines (no database)")
    klines = await get_kline_websocket(
        symbol="BTCUSDT",
        interval="1m", 
        max_klines=5,
        dbr=False,  # 不入库
        callback=kline_callback
    )
    
    # 示例2: 接收数据并入库（推荐的会话管理方式）
    logger.info("Example 2: Getting ETH 1m klines with database")
    from DatabaseOperator import get_db_session
    try:
        with get_db_session() as session:
            klines_with_db = await get_kline_websocket(
                symbol="ETHUSDT",
                interval="1m",
                dbr=True,
                session=session,
                max_klines=3,
                callback=kline_callback
            )
    except Exception as e:
        logger.error(f"Database operation error: {e}")
    
    return klines