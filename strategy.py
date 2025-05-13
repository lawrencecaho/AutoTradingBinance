# strategy.py

from database import Session, PriceDiff

def should_trade():
    session = Session()

    # 获取最近一次差额记录
    latest_diff = session.query(PriceDiff).order_by(PriceDiff.timestamp.desc()).first()
    decision = None

    # 示例策略：当涨幅超过100美元就买入，跌幅超过100美元就卖出（演示用）
    if latest_diff:
        if latest_diff.diff > 100:
            decision = ('BUY', latest_diff.current_price)
        elif latest_diff.diff < -100:
            decision = ('SELL', latest_diff.current_price)

    if decision:
        print(f"[Strategy] Decision: {decision[0]} at price {decision[1]}")
    else:
        print("[Strategy] No trade decision.")

    session.close()
    return decision
