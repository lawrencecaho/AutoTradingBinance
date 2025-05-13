# trader.py

def execute_trade(decision, quantity=0.001):
    if not decision:
        return

    action, price = decision

    # 模拟交易输出，真实交易需调用 Binance API
    print(f"[Trader] Executing {action} order at price {price}, quantity {quantity}")
    # 可加入数据库记录或调用实际交易接口
