# calculator.py

from database import Session, Price, BuyHistory, PriceDiff
from config import SYMBOL
import argparse

# 动态获取表名
Price.__tablename__ = f'price_data_{SYMBOL.lower()}'
BuyHistory.__tablename__ = f'buy_history_{SYMBOL.lower()}'
PriceDiff.__tablename__ = f'price_diff_{SYMBOL.lower()}'

def calculate_diff():
    session = Session()

    # 获取最新价格
    current_price = session.query(Price).order_by(Price.timestamp.desc()).first()
    if current_price:
        print(f"[Calculator] Current price: {current_price.price}")
    else:
        print("[Calculator] No current price data available.")
        session.close()
        return
    # 获取最后一次买入记录
    last_buy = session.query(BuyHistory).order_by(BuyHistory.timestamp.desc()).first()
    if last_buy:
        print(f"[Calculator] Last buy price: {last_buy.price}")
    else:
        print("[Calculator] No buy history available.")
        session.close()
        return
    # 计算差额

    if current_price and last_buy:
        diff = current_price.price - last_buy.price

        # 写入差额记录
        diff_entry = PriceDiff(diff=diff, current_price=current_price.price, buy_price=last_buy.price)
        session.add(diff_entry)
        session.commit()

        print(f"[Calculator] Price diff: {diff:.2f}")
    else:
        print("[Calculator] Not enough data to calculate diff.")

    session.close()

if __name__ == '__main__':
    # 添加命令行参数解析
    parser = argparse.ArgumentParser(description='Calculate price differences based on the latest data.')
    parser.add_argument('--dev', action='store_true', help='Run calculate_diff directly for debugging purposes')
    args = parser.parse_args()

    # 如果传递了 --dev 参数，直接调用 calculate_diff
    if args.dev:
        calculate_diff()
