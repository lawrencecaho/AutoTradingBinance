# app/ExchangeFetcher/fetcher.py

import argparse
import requests
import select
import sys
import time
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