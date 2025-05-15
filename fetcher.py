# fetcher.py

import requests
from database import Session, init_db, engine
from config import SYMBOL, StableUrl
import argparse
import time
from config import FETCH_INTERVAL_SECONDS
import sys
import select
from sqlalchemy import Table, MetaData

# 修改 fetch_price 函数以支持动态表名
metadata = MetaData()
Price = Table(
    f"price_data_{SYMBOL.lower()}",
    metadata,
    autoload_with=engine
)

# fetch_price 函数：从 Binance API 获取最新价格并存储到数据库
# 参数：无
# 返回值：存储的价格值
# 功能：
# 1. 构造 API 请求 URL
# 2. 发送 HTTP GET 请求获取价格数据
# 3. 将价格数据存储到数据库中
# 4. 打印存储的价格信息
# 5. 返回存储的价格值

def fetch_price():
    # 基于变量构造 API 的请求 URL
    url = f'{StableUrl}/price?symbol={SYMBOL}'
    
    # 发送 HTTP GET 请求以获取最新价格数据
    response = requests.get(url)
    data = response.json()  # 将响应解析为 JSON 格式
    
    # 提取价格并将其转换为浮点数
    price = float(data['price'])

    # 初始化数据库会话
    session = Session()
    
    # 创建价格记录并添加到数据库会话中
    price_entry = Price.insert().values(symbol=SYMBOL, price=price)
    session.execute(price_entry)
    
    # 提交事务以保存数据到数据库
    session.commit()
    
    # 关闭数据库会话以释放资源
    session.close()

    # 打印存储的价格信息
    print(f"[Fetcher] Stored price: {price}")
    return price

# 在 fetch_price 函数外部添加循环逻辑
if __name__ == '__main__':
    # 初始化数据库表
    init_db()

    # 使用 argparse 模块解析命令行参数
    parser = argparse.ArgumentParser(description='Fetch the latest price from Binance and optionally store it in the database.')
    parser.add_argument('--store', action='store_true', help='Store the fetched price in the database')
    args = parser.parse_args()

    print("Press 'q' and Enter to stop the fetcher.")

    while True:
        # 检测用户输入是否为 'q'
        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
            line = sys.stdin.readline().strip()
            if line.lower() == 'q':
                print("[Fetcher] Stopping fetcher.")
                break

        # 调用 fetch_price 函数获取价格
        price = fetch_price()

        # 根据命令行参数决定是否存储价格到数据库
        if args.store:
            print(f"[Fetcher] Price {price} has been stored in the database.")
        else:
            print(f"[Fetcher] Fetched price: {price}")

        # 等待指定的时间间隔
        time.sleep(FETCH_INTERVAL_SECONDS)
