# fetcher.py

import argparse
import requests
import select
import sys
import time
from datetime import datetime, timezone
from config import BINANCE_API_BASE_URL, DEFAULT_SYMBOL
from app.DatabaseOperator.pg_operator import Session, engine, init_db, insert_price, insert_kline
from DatabaseOperator.redis_operator import 
from DataProcessingCalculator.DataModificationModule import parse_kline

def fetch_price(Price):
    """
    从 Binance API 获取最新价格并存储到数据库
    参数:Price 表对象
    返回值:存储的价格值
    """
    try:
        symbol = get_active_symbol()  # 动态获取当前交易对
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

#命令行调用传入参数 store 则独立运行直到用户输入 'q' 停止。（不需要传入参数 store 也可以运行，也会自动存储数据）
if __name__ == '__main__':
    # 初始化数据库表
    #init_db()
    # 只反射一次表结构
    from sqlalchemy import Table, MetaData
    symbol = get_active_symbol()  # 动态获取当前交易对
    metadata = MetaData()
    Price = Table(
        f"price_data_{symbol.lower()}",
        metadata,
        autoload_with=engine
    )
    # 使用 argparse 模块解析命令行参数
    parser = argparse.ArgumentParser(description='Fetch the latest price from Binance and optionally store it in the database.')
    parser.add_argument('--store', action='store_true', help='Store the fetched price in the database')
    args = parser.parse_args()

    print("Press 'q' and Enter to stop the fetcher.")
    timeset = get_fetch_interval()  # 获取时间间隔
    print(f"[Fetcher] Fetching price every {timeset} seconds.")

    while True:
        # 检测用户输入是否为 'q'
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline().strip()
            if line.lower() == 'q':
                print("[Fetcher] Stopping fetcher.")
                break

        # 调用 fetch_price 函数获取价格
        price = fetch_price(Price)
        if price is not None:
            if args.store:
                print(f"[Fetcher] Price {price} has been stored in the database.")
            else:
                print(f"[Fetcher] Fetched price: {price}")

        # 等待指定的时间间隔
        
        
        time.sleep(float(timeset))

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