# app/DataProcessingCalculator/calculator.py
import argparse
import logging
from app.DatabaseOperator.pg_operator import Session, engine
from config import SYMBOL
from sqlalchemy import Table, MetaData
from datetime import datetime, timezone
from DataProcessingCalculator.DataAnalyze import StartCaculateMACD, analyze_data_and_store_emas

metadata = MetaData()
Price = Table(
    f"price_data_{SYMBOL.lower()}",
    metadata,
    autoload_with=engine
)
BuyHistory = Table(
    f"buy_history_{SYMBOL.lower()}",
    metadata,
    autoload_with=engine
)
PriceDiff = Table(
    f"price_diff_{SYMBOL.lower()}",
    metadata,
    autoload_with=engine
)

# calculate_diff 函数：计算最新价格与最后一次买入价格的差值
# 参数：无
# 功能：
# 1. 查询数据库中最新的价格记录
# 2. 查询数据库中最后一次买入记录
# 3. 计算价格差值并存储到数据库中
# 4. 打印价格差值信息
# 注意：如果没有价格记录或买入记录，函数会提前返回
def calculate_diff():
    session = Session()
    current_price = session.query(Price).order_by(Price.c.timestamp.desc()).first()
    if current_price:
        print(f"[Calculator] Current price: {current_price.price}")
    else:
        print("[Calculator] No current price data available.")
        session.close()
        return

    last_buy = session.query(BuyHistory).order_by(BuyHistory.c.timestamp.desc()).first()
    if last_buy:
        print(f"[Calculator] Last buy price: {last_buy.price}")
    else:
        print("[Calculator] No buy history available.")
        session.close()
        return

    if current_price and last_buy:
        diff = current_price.price - last_buy.price
        diff_entry = PriceDiff.insert().values(
            diff=diff,
            current_price=current_price.price,
            buy_price=last_buy.price,
            timestamp=datetime.now(timezone.utc)
        )
        session.execute(diff_entry)
        session.commit()

        print(f"[Calculator] Price diff: {diff:.2f}")

    session.close()

if __name__ == '__main__':
    # 添加命令行参数解析
    parser = argparse.ArgumentParser(description='Calculate price differences based on the latest data.')
    parser.add_argument('--dev', action='store_true', help='Run calculate_diff directly for debugging purposes')
    args = parser.parse_args()

    # 如果传递了 --dev 参数，直接调用 calculate_diff
    if args.dev:
        calculate_diff()
