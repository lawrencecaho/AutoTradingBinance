# strategy.py

import logging
from database import Session, Price
import pandas as pd

# 初始化日志
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def fetch_price_history():
    """
    从数据库中获取全部历史价格记录，按时间升序排列。
    用于计算移动平均线。
    """
    session = Session()
    try:
        prices = session.query(Price).order_by(Price.timestamp.asc()).all()
        price_data = [{"timestamp": p.timestamp, "price": p.price} for p in prices]
        return pd.DataFrame(price_data)
    except Exception as e:
        logging.error(f"[Error] 获取价格历史时发生错误: {e}")
        return pd.DataFrame()  # 返回空的 DataFrame 以避免后续代码崩溃
    finally:
        session.close()

def compute_ema_signals(price_df):
    """
    基于历史价格数据计算 EMA50 和 EMA200，并判断是否出现金叉或死叉。

    返回：
        ('BUY', 当前价格) 表示金叉信号；
        ('SELL', 当前价格) 表示死叉信号；
        None 表示无交易信号。
    """
    if len(price_df) < 200:
        logging.warning("[Strategy] 数据不足，至少需要200条价格记录用于计算 EMA。")
        return None

    # 计算 EMA50 和 EMA200
    price_df["EMA50"] = price_df["price"].ewm(span=50, adjust=False).mean()
    price_df["EMA200"] = price_df["price"].ewm(span=200, adjust=False).mean()

    # 取最近两条记录，判断交叉情况
    latest = price_df.iloc[-1]
    previous = price_df.iloc[-2]

    # 判断是否发生金叉或死叉
    if previous["EMA50"] < previous["EMA200"] and latest["EMA50"] > latest["EMA200"]:
        logging.info("[Strategy] 检测到金叉：EMA50 上穿 EMA200。")
        return ("BUY", latest["price"])
    elif previous["EMA50"] > previous["EMA200"] and latest["EMA50"] < latest["EMA200"]:
        logging.info("[Strategy] 检测到死叉：EMA50 下穿 EMA200。")
        return ("SELL", latest["price"])
    else:
        logging.info("[Strategy] 未检测到交易信号。")
        return None

def should_trade():
    """
    主策略入口。获取价格历史并判断是否存在买卖信号。

    返回：
        ('BUY', 当前价格) 或 ('SELL', 当前价格) 或 None。
    """
    price_df = fetch_price_history()

    if price_df.empty:
        logging.warning("[Strategy] 无法获取价格历史，跳过交易判断。")
        return None

    decision = compute_ema_signals(price_df)

    if decision:
        logging.info(f"[Strategy] Decision: {decision[0]} at price {decision[1]}")
    else:
        logging.info("[Strategy] No trade decision.")

    Session.close() # 重点关注
    return decision
