# calculator.py

from database import Session, Price, BuyHistory, PriceDiff

def calculate_diff():
    session = Session()

    # 获取最新价格
    current_price = session.query(Price).order_by(Price.timestamp.desc()).first()
    # 获取最后一次买入记录
    last_buy = session.query(BuyHistory).order_by(BuyHistory.timestamp.desc()).first()

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
