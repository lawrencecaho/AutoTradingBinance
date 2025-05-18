import pandas as pd
import logging

from database import Session, dbselect_common, dbget_common, dbinsert_common, dbupdate_common


def StartCaculate():
    """
    主函数，获取K线数据并计算MACD指标
    """
    # 获取K线数据
    Kline_data = dbselect_common(Session())
    if Kline_data is None:
        logging.error("获取K线数据失败")
        return

    # 将K线数据转换为DataFrame
    df = kline_to_dataframe(Kline_data)

    # 计算MACD指标
    df = calculate_macd(df)

    # 打印结果
    print(df[['open_time', 'close', 'macd']])


def calculate_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def calculate_macd(df):
    """
    计算 MACD 指标，并添加到原始 DataFrame 中。
    要求 df 有 'close' 列（收盘价）。
    """
    df['ema12'] = calculate_ema(df['close'], 12)
    df['ema26'] = calculate_ema(df['close'], 26)
    df['dif'] = df['ema12'] - df['ema26']
    df['dea'] = calculate_ema(df['dif'], 9)
    df['macd'] = 2 * (df['dif'] - df['dea'])
    return df

def kline_to_dataframe(kline_data):
    """
    将 Binance kline 原始列表转换为 pandas DataFrame
    """
    df = pd.DataFrame(kline_data, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base_vol', 'taker_buy_quote_vol', 'ignore'
    ])
    # 转换类型
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
    df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
    df['close'] = pd.to_numeric(df['close'])
    return df