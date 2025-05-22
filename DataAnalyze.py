import pandas as pd
import logging
from config import SYMBOL, FETCH_INTERVAL_SECONDS
from database import Session, dbselect_common, dbinsert_common, dbupdate_common


def StartCaculate():
    """
    主函数，获取K线数据并计算MACD指标
    """
    # 获取K线数据
    session = Session()
    # 使用原始SYMBOL大小写构建表名
    KLine_data = dbselect_common(session, f"KLine_{SYMBOL}", "symbol", SYMBOL)
    if KLine_data is None:
        logging.error("获取K线数据失败")
        return

    # 将K线数据转换为DataFrame
    df = KLine_to_dataframe(KLine_data)

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

def KLine_to_dataframe(KLine_data):
    """
    将数据库返回的K线数据 (元组列表) 转换为 pandas DataFrame
    """
    # 基于 database.py中 insert_KLine 函数的列顺序和用户提供的信息
    columns = [
        'id', 'symbol', 'open', 'high', 'low', 'close', 'volume',
        'open_time', 'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base_vol', 'taker_buy_quote_vol', 'timestamp'
    ]
    df = pd.DataFrame(KLine_data, columns=columns)
    
    # 转换类型
    # 如果 open_time, close_time, timestamp 从数据库取出时已是 datetime 对象，
    # pd.to_datetime() 仍然是安全的，可以确保它们是 pandas 的 datetime64[ns] 类型。
    # 如果它们是标准格式的字符串，pd.to_datetime() 也能正确解析。
    df['open_time'] = pd.to_datetime(df['open_time'])
    df['close_time'] = pd.to_datetime(df['close_time'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # 将数值列转换为数字类型
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 
                    'quote_asset_volume', 'num_trades', 
                    'taker_buy_base_vol', 'taker_buy_quote_vol']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col])
        
    return df

def analyze_data():
    """
    分析存储在数据库中的K线数据。
    """
    session = Session()
    # 获取logger实例，main函数中已配置basicConfig
    logger = logging.getLogger(__name__) 
    try:
        logger.info(f"开始分析数据，符号: {SYMBOL}")
        # 构建表名，使用原始SYMBOL大小写
        KLine_table_name = f"KLine_{SYMBOL}"
        logger.info(f"查询表: {KLine_table_name} 中 symbol 为 {SYMBOL} 的数据")
        
        KLine_data = dbselect_common(session, KLine_table_name, "symbol", SYMBOL)
        
        logger.info(f"从数据库获取的 KLine_data 类型: {type(KLine_data)}")
        if hasattr(KLine_data, '__len__'):
            logger.info(f"KLine_data 长度: {len(KLine_data)}")
        
        if KLine_data and isinstance(KLine_data, list) and len(KLine_data) > 0:
            logger.info(f"KLine_data (前几条记录示例): {KLine_data[:min(3, len(KLine_data))]}")
        elif KLine_data is not None:
             logger.info(f"KLine_data (内容): {KLine_data}")

        if not KLine_data: 
            logger.warning(f"未找到符号为 {SYMBOL} 的K线数据，或数据为空。KLine_data: {KLine_data}")
            return

        logger.info("将K线数据转换为DataFrame...")
        df = KLine_to_dataframe(KLine_data)
        
        logger.info("DataFrame转换完成。DataFrame信息:")
        logger.info(f"DataFrame (前5行):\\n{df.head().to_string()}")
        logger.info(f"DataFrame dtypes:\\n{df.dtypes.to_string()}")

        if df.empty:
            logger.warning(f"转换后的DataFrame为空，符号: {SYMBOL}")
            return
        
        if 'close' not in df.columns:
            logger.error("'close'列不在DataFrame中。无法计算MACD。")
            logger.info(f"DataFrame 列: {df.columns}")
            return

        if df['close'].isnull().all():
            logger.warning("DataFrame中的'close'列全部为NaN。MACD计算可能返回全部NaN。")
        elif df['close'].isnull().any():
            logger.warning("DataFrame中的'close'列包含NaN值。这可能影响MACD计算。")
        
        logger.info("计算MACD指标...")
        df = calculate_macd(df)
        logger.info("MACD指标计算完成。")
        # 动态构建要显示的列，确保它们存在于DataFrame中
        macd_related_cols = ['open_time', 'close', 'macd']
        existing_macd_debug_cols = [col for col in ['ema12', 'ema26', 'dif', 'dea'] if col in df.columns]
        display_cols_after_macd = macd_related_cols + existing_macd_debug_cols
        logger.info(f"计算MACD后的DataFrame (前5行，相关列):\\n{df[display_cols_after_macd].head().to_string()}")

        logger.info("准备打印结果...")
        required_print_cols = ['open_time', 'close', 'macd']
        missing_cols = [col for col in required_print_cols if col not in df.columns]
        if missing_cols:
            logger.error(f"DataFrame中缺少用于打印的列: {missing_cols}")
            logger.info(f"可用列: {df.columns}")
            return
        
        print("\\n--- 分析结果 ---")
        print(df[required_print_cols])
        print("--- 分析结果结束 ---\\n")
        logger.info("结果已打印到控制台。")

    except Exception as e:
        logger.error(f"分析数据时发生严重错误: {e}", exc_info=True) # exc_info=True 会记录完整的错误回溯
    finally:
        logger.info("关闭数据库会话。")
        session.close()

def main():
    """
    用于测试调用的主函数。
    """
    # 配置日志，以便在直接运行此脚本时能看到输出
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info("开始执行 DataAnalyze.py 的 main 函数...")
    
    # 你也可以在这里调用 StartCaculate() 如果它是你想测试的主要流程
    # logger.info("调用 StartCaculate()...")
    # StartCaculate()
    # logger.info("StartCaculate() 执行完毕。")

    logger.info("调用 analyze_data()...")
    analyze_data()
    logger.info("analyze_data() 执行完毕。")
    
    logger.info("DataAnalyze.py 的 main 函数执行完毕。")

if __name__ == "__main__":
    main()
