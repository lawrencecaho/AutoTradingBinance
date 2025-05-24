# DataAnalyze.py
import pandas as pd
import logging
from config import SYMBOL, FETCH_INTERVAL_SECONDS
from database import (
    Session, 
    engine,  # Assuming engine is correctly configured for PostgreSQL
    dbget_kline, # Changed from dbselect_common to dbget_kline
)
from datetime import datetime, timezone
from sqlalchemy import Table, Column, DateTime, Float, MetaData, inspect, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

"""
| MA 类型 | 意义（基于每根 K 线）   | `limit` 最小值 | 示例 API 参数 (`interval=1h
| ----- | -------------- | ----------- | ------------------------- | ----------------------------- |
| MA5   | 最近 5 根 K 线均值   | 5           | `limit=5`                 | 快速变化，适合短线分析          |
| MA10  | 最近 10 根 K 线均值  | 10          | `limit=10`                | 短期趋势判断                   |
| MA20  | 最近 20 根 K 线均值  | 20          | `limit=20`                | 常见中期趋势线              |
| MA30  | 最近 30 根 K 线均值  | 30          | `limit=30`                | 比 MA20 平滑                     |
| MA50  | 最近 50 根 K 线均值  | 50          | `limit=50`                | 可靠的中长期线                |
| MA100 | 最近 100 根 K 线均值 | 100         | `limit=100`               | 代表长期趋势                    |
| MA200 | 最近 200 根 K 线均值 | 200         | `limit=200`（需分批获取）   | 经典长期趋势线，Binance 最多返回 1000 条 |
"""

def CheckPreCalculator():
    """
    检查数据库表中的最新列距离现在时间距离

    """
    # 这里可以添加一些简单的检查逻辑，比如检查数据库连接等
    try:
        session = Session()
        session.close()
        print("计算器检查通过")
    except Exception as e:
        print(f"计算器检查失败: {e}")

def StartCaculateMACD(): # This function seems to be more for MACD, let's keep analyze_data for MAs
    """
    主函数，获取K线数据并计算MACD指标 (当前主要用于MACD，EMA存储在analyze_data中)
    """
    session = Session()
    try:
        KLine_data = dbget_kline(session, f"KLine_{SYMBOL}", SYMBOL, order_by_column='open_time', ascending=True)
        if KLine_data is None:
            logging.error(f"获取K线数据失败 (StartCaculateMACD for {SYMBOL})")
            return

        df = KLine_to_dataframe(KLine_data)
        if df.empty:
            logging.warning(f"K线数据转换后DataFrame为空 (StartCaculateMACD for {SYMBOL})")
            return
        
        # Ensure DataFrame is sorted by open_time for consistent calculations if needed
        df.sort_values(by='open_time', inplace=True)

        df = calculate_macd(df)
        # logging.info(f"MACD data for {SYMBOL}:\n{df[['open_time', 'close', 'macd']].tail()}")
        # No printing to terminal as per user request for MA data. 
        # If MACD also should not be printed, the line above can be fully removed or logged.
    except Exception as e:
        logging.error(f"Error in StartCaculateMACD for {SYMBOL}: {e}", exc_info=True)
    finally:
        session.close()


def calculate_ema(series, span):
    # Ensure min_periods is at least 1 so that it doesn't return NaN for the first row if span is 1
    # and to allow calculation to start as soon as there's data.
    # Pandas default for min_periods in ewm is 0, but for mean calculation, it effectively becomes 1.
    # Using min_periods=span would mean waiting for `span` periods to get the first EMA value.
    # Using min_periods=1 (or 0 which defaults to 1 for mean) allows EMA to be calculated from the first data point.
    return series.ewm(span=span, adjust=False, min_periods=1).mean()

def calculate_macd(df):
    """
    计算 MACD 指标，并添加到原始 DataFrame 中。
    要求 df 有 'close' 列（收盘价）。
    """
    if 'close' not in df.columns:
        logging.error("'close' column not found in DataFrame. Cannot calculate MACD.")
        return df
    if df['close'].isnull().all():
        logging.warning("All 'close' values are NaN. MACD calculation will result in NaNs.")
        # Add empty columns to prevent key errors later if other code expects them
        for col_name in ['ema12', 'ema26', 'dif', 'dea', 'macd']:
            df[col_name] = pd.NA 
        return df

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
    columns = [
        'symbol', 'open', 'high', 'low', 'close', 'volume',
        'open_time', 'close_time', 'quote_asset_volume', 'num_trades',
        'taker_buy_base_vol', 'taker_buy_quote_vol', 'timestamp'
    ]
    df = pd.DataFrame(KLine_data, columns=columns)
    
    numeric_cols = ['open', 'high', 'low', 'close', 'volume', 
                    'quote_asset_volume', 'num_trades', 
                    'taker_buy_base_vol', 'taker_buy_quote_vol']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce') # Coerce errors to NaN

    time_cols = ['open_time', 'close_time', 'timestamp']
    for col in time_cols:
        # 保留时区信息，如果存在
        df[col] = pd.to_datetime(df[col], errors='coerce', utc=True) 
        
    return df

def calculate_multiple_emas(df, periods=[5, 10, 20, 30]):
    """
    Calculates multiple EMAs for the 'close' price and adds them to the DataFrame.
    """
    if 'close' not in df.columns:
        logging.error("'close' column not found in DataFrame. Cannot calculate EMAs.")
        return df
    if df['close'].isnull().all():
        logging.warning("All 'close' values are NaN. EMA calculations will result in NaNs.")
        for period in periods:
            df[f'ema{period}'] = pd.NA # Assign pandas NA for consistency
        return df

    for period in periods:
        df[f'ema{period}'] = calculate_ema(df['close'], period)
    logging.info(f"Calculated EMAs for periods: {periods} for symbol {SYMBOL}")
    return df

def create_ma_table_if_not_exists(engine, table_name_str):
    """
    Creates a table for storing MA/EMA data if it doesn't already exist.
    The table will have open_time as the primary key.
    Column names for EMAs are fixed as ema5, ema10, ema20, ema30.
    Now also includes MACD related columns: ema12, ema26, dif, dea, macd.
    And ROC columns for all EMAs and MACD components.
    """
    metadata = MetaData()
    inspector = inspect(engine)
    
    # Define all columns that should be in the table
    # Keep existing columns and add new ROC columns
    # Sort alphabetically for consistency and readability
    table_columns = [
        Column('open_time', DateTime(timezone=True), primary_key=True),  # 确保使用带时区的DateTime
        Column('close', Float, nullable=False),
        Column('dea', Float, nullable=True),
        Column('dea_roc', Float, nullable=True), # New
        Column('dif', Float, nullable=True),
        Column('dif_roc', Float, nullable=True), # New
        Column('ema5', Float, nullable=True),
        Column('ema5_roc', Float, nullable=True), # New
        Column('ema10', Float, nullable=True),
        Column('ema10_roc', Float, nullable=True), # New
        Column('ema12', Float, nullable=True),
        Column('ema20', Float, nullable=True),
        Column('ema20_roc', Float, nullable=True), # New
        Column('ema26', Float, nullable=True),
        Column('ema30', Float, nullable=True),
        Column('ema30_roc', Float, nullable=True), # New
        Column('macd', Float, nullable=True),
        Column('macd_roc', Float, nullable=True) # New
    ]

    if not inspector.has_table(table_name_str):
        Table(table_name_str, metadata, *table_columns)
        metadata.create_all(engine)
        logging.info(f"Table {table_name_str} created successfully with all ROC columns.")
    else:
        # Check for missing columns and add them if necessary
        existing_table = Table(table_name_str, metadata, autoload_with=engine)
        existing_column_names = [col.name for col in existing_table.columns]
        
        # Find which of the defined columns are missing
        missing_cols_to_add = []
        for defined_col in table_columns:
            if defined_col.name not in existing_column_names:
                missing_cols_to_add.append(defined_col)
        
        if missing_cols_to_add:
            logging.info(f"Table {table_name_str} exists. Attempting to add missing columns: {[col.name for col in missing_cols_to_add]}")
            with engine.connect() as connection:
                for col_to_add in missing_cols_to_add:
                    # Construct the ADD COLUMN SQL statement carefully
                    col_type_str = str(col_to_add.type.compile(engine.dialect))
                    # Default to NULLABLE if not specified, though our Float columns are nullable=True
                    alter_sql = f"ALTER TABLE {table_name_str} ADD COLUMN IF NOT EXISTS {col_to_add.name} {col_type_str}"
                    try:
                        connection.execute(text(alter_sql))
                        logging.info(f"Successfully added column {col_to_add.name} to {table_name_str}.")
                    except Exception as e_alter:
                        logging.error(f"Failed to add column {col_to_add.name} to {table_name_str}: {e_alter}")
                connection.commit() # Commit after all ALTER TABLE statements
            # Re-autoload the table to reflect changes for the return value
            metadata.clear() # Clear old metadata
            existing_table = Table(table_name_str, metadata, autoload_with=engine)
            logging.info(f"Table {table_name_str} schema updated.")
        # else:
            # logging.debug(f"Table {table_name_str} already exists and has all required columns.")

    return Table(table_name_str, metadata, autoload_with=engine)

def calculator_roc(df, col, epsilon=1e-8):
    return ((df[col] - df[col].shift(1)) / (df[col].shift(1).abs() + epsilon)) * 100

def analyze_data_and_store_emas():
    """
    Fetches K-line data, calculates specified EMAs (5, 10, 20, 30), 
    and stores them in a PostgreSQL database table named ma_<SYMBOL>.
    Uses INSERT ON CONFLICT DO UPDATE (upsert) for PostgreSQL.
    """
    session = Session()
    logger = logging.getLogger(__name__) 
    try:
        logger.info(f"开始分析数据并存储EMA，符号: {SYMBOL}")
        
        KLine_table_name = f"KLine_{SYMBOL}"
        # logger.debug(f"查询表: {KLine_table_name} 中 symbol 为 {SYMBOL} 的数据")
        
        # 检查表是否存在，如果不存在则创建
        from database import create_kline_table_if_not_exists
        create_kline_table_if_not_exists(engine, SYMBOL)
        
        # Use the new dbget_kline function, ensuring data is sorted by open_time ascending
        KLine_data = dbget_kline(session, KLine_table_name, SYMBOL, order_by_column='open_time', ascending=True)
        
        if not KLine_data: 
            logger.warning(f"未找到符号为 {SYMBOL} 的K线数据，或数据为空。")
            return

        # logger.debug("将K线数据转换为DataFrame...")
        df = KLine_to_dataframe(KLine_data)
        
        if df.empty:
            logger.warning(f"转换后的DataFrame为空，符号: {SYMBOL}")
            return
        
        # IMPORTANT: Ensure DataFrame is sorted by open_time for correct EMA calculation
        df.sort_values(by='open_time', inplace=True)
        # logger.debug(f"DataFrame sorted by open_time. Head:\n{df.head().to_string()}")


        if 'close' not in df.columns or df['close'].isnull().all():
            logger.error(f"'close'列不存在或全部为NaN，无法计算EMA。DataFrame columns: {df.columns}")
            return

        # logger.debug("计算EMA指标 (5, 10, 20, 30)...")
        ema_periods_to_calculate = [5, 10, 20, 30]
        df = calculate_multiple_emas(df, periods=ema_periods_to_calculate)
        
        # Calculate MACD as well to store it in the same table
        logger.info("Calculating MACD indicators...")
        df = calculate_macd(df) # calculate_macd adds ema12, ema26, dif, dea, macd

        # Calculate ROC for EMAs and MACD components
        logger.info("Calculating ROC for EMAs and MACD components...")
        roc_source_columns = []
        for period in ema_periods_to_calculate:
            roc_source_columns.append(f'ema{period}')
        roc_source_columns.extend(['macd', 'dif', 'dea'])

        for col_name in roc_source_columns:
            if col_name in df.columns and not df[col_name].isnull().all():
                df[f'{col_name}_roc'] = calculator_roc(df, col_name)
            else:
                df[f'{col_name}_roc'] = pd.NA # Assign pandas NA if source column is missing or all NaN
                logger.warning(f"Source column {col_name} for ROC calculation is missing or all NaN. {col_name}_roc set to NA.")


        # Columns to select for storage, must match create_ma_table_if_not_exists
        # Ensure all ROC columns are included
        cols_to_store = [
            'open_time', 'close', 
            'ema5', 'ema10', 'ema20', 'ema30', 
            'ema12', 'ema26', 'dif', 'dea', 'macd',
            'ema5_roc', 'ema10_roc', 'ema20_roc', 'ema30_roc', # EMA ROCs
            'macd_roc', 'dif_roc', 'dea_roc' # MACD component ROCs
        ]
        
        missing_cols = [col for col in cols_to_store if col not in df.columns]
        if missing_cols:
            # This case should ideally be handled by calculate_multiple_emas adding NA columns
            logger.error(f"DataFrame中缺少必要的列进行存储: {missing_cols}. 可用列: {df.columns}")
            return

        data_to_store_df = df[cols_to_store].copy()
        # Replace Pandas NaT/NaN with None for SQL compatibility, especially for nullable Float columns
        data_to_store_df = data_to_store_df.where(pd.notnull(data_to_store_df), None)
        
        # Drop rows where 'open_time' or 'close' is None (or NaT) as they are essential
        data_to_store_df.dropna(subset=['open_time', 'close'], inplace=True)


        if data_to_store_df.empty:
            logger.warning(f"没有有效的EMA数据行可供存储 (after NaN/NaT handling)，符号: {SYMBOL}")
            return

        ma_db_table_name = f"ma_{SYMBOL.lower()}" # Consistent lowercase table name
        # logger.debug(f"准备将数据写入数据库表: {ma_db_table_name}")
        
        ma_table = create_ma_table_if_not_exists(engine, ma_db_table_name)
        
        records_to_insert = data_to_store_df.to_dict(orient='records')

        if not records_to_insert:
            logger.info(f"没有记录需要插入/更新到表 {ma_db_table_name}.")
            return

        logger.info(f"共 {len(records_to_insert)} 条有效记录准备插入/更新到 {ma_db_table_name}.")

        with engine.connect() as connection:
            trans = connection.begin()
            try:
                for record_dict in records_to_insert:
                    # Ensure 'open_time' is Python datetime, already handled by KLine_to_dataframe + to_dict
                    # Filter record_dict to only include keys that are actual columns in ma_table
                    valid_record = {key: value for key, value in record_dict.items() if key in ma_table.columns.keys()}
                    
                    if not valid_record or 'open_time' not in valid_record or valid_record['open_time'] is None:
                        logger.warning(f"Skipping invalid record for upsert: {record_dict}")
                        continue

                    stmt = pg_insert(ma_table).values(valid_record)
                    
                    # Define columns to update on conflict, excluding the primary key 'open_time'
                    # and only if the column exists in the current valid_record being processed
                    update_values = {
                        col.name: stmt.excluded[col.name]
                        for col in ma_table.columns 
                        if col.name != 'open_time' and col.name in valid_record
                    }
                    
                    if update_values: # Only add set_ if there are columns to update
                        stmt = stmt.on_conflict_do_update(
                            index_elements=['open_time'], 
                            set_=update_values
                        )
                    else: # If no columns to update (e.g., only PK was inserted and it conflicts)
                        stmt = stmt.on_conflict_do_nothing(index_elements=['open_time'])
                    
                    connection.execute(stmt)
                trans.commit()
                logger.info(f"成功将 {len(records_to_insert)} 条EMA数据插入/更新到表 {ma_db_table_name}")
            except Exception as e_inner:
                trans.rollback()
                logger.error(f"插入/更新数据到 {ma_db_table_name} 时发生数据库错误: {e_inner}", exc_info=True)
                # Do not re-raise here if main loop should continue for other symbols or operations
            finally:
                # The connection is automatically closed when exiting the 'with engine.connect() as connection:' block
                pass


    except Exception as e:
        logger.error(f"在 analyze_data_and_store_emas 中分析和存储EMA数据时发生错误: {e}", exc_info=True)
    finally:
        # logger.debug("关闭数据库会话 (analyze_data_and_store_emas)。")
        session.close()

def main():
    """
    用于测试调用的主函数。
    """
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[logging.StreamHandler()]) # Ensure logs go to console
    logger = logging.getLogger(__name__) # Get logger for main
    logger.info("开始执行 DataAnalyze.py 的 main 函数...")
    
    logger.info("调用 StartCaculateMACD() (主要用于MACD计算)...")
    StartCaculateMACD()
    logger.info("StartCaculateMACD() 执行完毕。")

    logger.info("调用 analyze_data_and_store_emas() (用于EMA计算和存储)...")
    analyze_data_and_store_emas() # Renamed function
    logger.info("analyze_data_and_store_emas() 执行完毕。")
    
    logger.info("DataAnalyze.py 的 main 函数执行完毕。")

if __name__ == "__main__":
    main()
