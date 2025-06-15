from typing import List, Optional, Any, Dict # Add Dict here
from pydantic import BaseModel # Ensure BaseModel is imported
# from fastapi import FastAPI # FastAPI instance will be in main.py
from fastapi import APIRouter, Depends # Import APIRouter
import pandas as pd
from sqlalchemy import Table, MetaData, select, inspect # inspect 用于检查表是否存在
from datetime import datetime

# 假设 database.py 和 config.py 在父目录中
# 如果您的项目结构不同，请调整这些导入
import sys
import os
# 将父目录添加到sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import engine # engine 是必需的, Session 可能不需要在此文件中直接使用
from config import SYMBOL # Ensure SYMBOL is imported
import logging # Ensure logging is imported
from myfastapi.auth import get_current_user_from_token # MODIFIED: Import from myfastapi.auth
logger = logging.getLogger(__name__)

# 调整后的 Pydantic 模型
class MAData(BaseModel): # 用于主要的EMA及其ROC
    ema5: List[Optional[float]]
    ema5_roc: List[Optional[float]]
    ema10: List[Optional[float]]
    ema10_roc: List[Optional[float]]
    ema20: List[Optional[float]]
    ema20_roc: List[Optional[float]]
    ema30: List[Optional[float]]
    ema30_roc: List[Optional[float]]

class MACDData(BaseModel): # 无需更改，已正确
    dif: List[Optional[float]]
    dif_roc: List[Optional[float]]
    dea: List[Optional[float]]
    dea_roc: List[Optional[float]]
    macd: List[Optional[float]]
    macd_roc: List[Optional[float]]

class EMAData(BaseModel): # 用于其他EMA，例如构成MACD的EMA
    ema12: List[Optional[float]]
    ema26: List[Optional[float]]

class CoinData(BaseModel):
    dates: List[str]
    values: List[List[Optional[float]]] # OHLCV
    ma: MAData
    macd: MACDData
    ema: EMAData # 其他EMA

class CoinAPIResponse(BaseModel):
    CoinData: CoinData

# app = FastAPI() # Remove this line
router = APIRouter() # Create an APIRouter instance

# 将NaN/NaT转换为None以进行JSON序列化的辅助函数
def nan_to_none(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value

def series_to_list(series: pd.Series) -> List[Optional[float]]:
    # Ensure the series is not empty and handle potential all-NaN cases gracefully
    if series.empty:
        return []
    return [nan_to_none(x) for x in series.tolist()]

# @app.get("/kline-ma-cd-data", response_model=CoinAPIResponse)
@router.get("/kline-ma-cd-data", response_model=CoinAPIResponse, tags=["Echarts Data"]) # Change app to router, add tags for better Swagger UI organization
async def get_kline_data_from_db(current_user: Dict[str, Any] = Depends(get_current_user_from_token)):
    print("!!! ECHARTS: get_kline_data_from_db FUNCTION ENTERED (via print) !!!")
    print(f"!!! ECHARTS: SYMBOL from config: '{SYMBOL}' (via print) !!!")
    logging.getLogger().critical("!!! ECHARTS: get_kline_data_from_db FUNCTION ENTERED (via root logger) !!!")
    logging.getLogger().info(f"!!! ECHARTS: SYMBOL from config: '{SYMBOL}' (via root logger) !!!")
    logger.critical("!!! ECHARTS: get_kline_data_from_db FUNCTION ENTERED (via named logger myfastapi.echarts) !!!")
    logger.info(f"Attempting to fetch K-line data for SYMBOL: {SYMBOL} (via named logger myfastapi.echarts)")
    try:
        kline_table_name = f"KLine_{SYMBOL}"
        ma_table_name = f"ma_{SYMBOL.lower()}"
        logger.info(f"Using K-line table: {kline_table_name}, MA table: {ma_table_name}")
        
        metadata = MetaData()
        inspector = inspect(engine)

        kline_table_exists = inspector.has_table(kline_table_name)
        ma_table_exists = inspector.has_table(ma_table_name)
        logger.info(f"K-line table '{kline_table_name}' exists: {kline_table_exists}")
        logger.info(f"MA table '{ma_table_name}' exists: {ma_table_exists}")

        if not kline_table_exists or not ma_table_exists:
            logger.warning(f"One or both tables do not exist. K-line table: {kline_table_name}, MA table: {ma_table_name}.")
            return CoinAPIResponse(
                CoinData=CoinData(
                    dates=[],
                    values=[],
                    ma=MAData(ema5=[], ema5_roc=[], ema10=[], ema10_roc=[], ema20=[], ema20_roc=[], ema30=[], ema30_roc=[]),
                    macd=MACDData(dif=[], dif_roc=[], dea=[], dea_roc=[], macd=[], macd_roc=[]),
                    ema=EMAData(ema12=[], ema26=[])
                )
            )

        kline_table = Table(kline_table_name, metadata, autoload_with=engine)
        ma_table = Table(ma_table_name, metadata, autoload_with=engine)

        # 使用 engine 执行查询
        with engine.connect() as connection:
            kline_stmt = select(
                kline_table.c.open_time,
                kline_table.c.open,
                kline_table.c.high,
                kline_table.c.low,
                kline_table.c.close,
                kline_table.c.volume
            ).order_by(kline_table.c.open_time.asc())
            kline_data = pd.read_sql(kline_stmt, connection)

            ma_stmt = select(ma_table).order_by(ma_table.c.open_time.asc())
            ma_data = pd.read_sql(ma_stmt, connection)
            
            logger.info(f"Fetched kline_data. Empty: {kline_data.empty}. Rows: {len(kline_data)}")
            if not kline_data.empty:
                logger.debug(f"kline_data head:\\n{kline_data.head()}")
            logger.info(f"Fetched ma_data. Empty: {ma_data.empty}. Rows: {len(ma_data)}")
            if not ma_data.empty:
                logger.debug(f"ma_data head:\\n{ma_data.head()}")

        if kline_data.empty or ma_data.empty:
            logger.info(f"For {SYMBOL}, one or both tables have no data. Kline empty: {kline_data.empty}, MA empty: {ma_data.empty}")
            return CoinAPIResponse(
                CoinData=CoinData(
                    dates=[],
                    values=[],
                    ma=MAData(ema5=[], ema5_roc=[], ema10=[], ema10_roc=[], ema20=[], ema20_roc=[], ema30=[], ema30_roc=[]),
                    macd=MACDData(dif=[], dif_roc=[], dea=[], dea_roc=[], macd=[], macd_roc=[]),
                    ema=EMAData(ema12=[], ema26=[])
                )
            )
        
        # 修复：关键问题在于处理K线数据中的UTC时区和MA数据中的无时区 datetime64[ns]
        # 1. 处理K线数据
        logger.info(f"K线数据时区信息 - 初始 dtype: {kline_data['open_time'].dtype}")
        # 将K线数据转换为不带时区的日期时间，确保正确处理UTC时间
        if str(kline_data['open_time'].dtype).endswith('UTC'):
            # 如果K线数据带有UTC时区，将时区信息移除，但保留UTC时间值
            logger.info("从K线的open_time中移除时区信息...")
            # 方法1：将UTC日期时间转换为本地日期时间
            kline_data['open_time_local'] = kline_data['open_time'].dt.tz_convert(None)
            # 使用本地时间合并
            merge_key_kline = 'open_time_local'
        else:
            # 如果K线数据没有时区信息，直接使用原始列
            merge_key_kline = 'open_time'
        
        # 2. 处理MA数据
        logger.info(f"MA数据时区信息 - 初始 dtype: {ma_data['open_time'].dtype}")
        # 将MA数据保持原样，因为它已经是无时区的datetime64[ns]
        merge_key_ma = 'open_time'
        
        # 3. 创建合并键（基于日期字符串）
        logger.info("创建基于日期字符串的合并键...")
        # 将两个数据集中的日期转换为相同格式的字符串
        date_format = '%Y-%m-%d %H:%M:%S'
        kline_data['merge_key'] = kline_data[merge_key_kline].dt.strftime(date_format)
        ma_data['merge_key'] = ma_data[merge_key_ma].dt.strftime(date_format)
        
        # 4. 检查重叠日期
        kline_dates = set(kline_data['merge_key'])
        ma_dates = set(ma_data['merge_key'])
        common_dates = kline_dates.intersection(ma_dates)
        
        logger.info(f"K线数据中的唯一日期数: {len(kline_dates)}")
        logger.info(f"MA数据中的唯一日期数: {len(ma_dates)}")
        logger.info(f"两个数据集中共有的日期数: {len(common_dates)}")
        
        # 5. 基于字符串日期合并数据
        logger.info("尝试基于字符串日期合并数据...")
        merged_df = pd.merge(
            kline_data, 
            ma_data, 
            on='merge_key',
            how='inner', 
            suffixes=['_kline', '_ma']
        )
        
        logger.info(f"合并结果: {len(merged_df)} 行")
        
        if merged_df.empty:
            logger.warning("合并后的DataFrame为空。尝试另一种合并方法或返回部分数据...")
            
            # 如果合并失败，使用K线数据提供部分响应
            dates = kline_data['open_time'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
            values = []
            for _, row in kline_data.iterrows():
                values.append([
                    nan_to_none(row['open']), 
                    nan_to_none(row['close']), 
                    nan_to_none(row['low']), 
                    nan_to_none(row['high']), 
                    nan_to_none(row['volume'])
                ])
            
            # 创建空的MA数据
            ma_response = MAData(
                ema5=[], ema5_roc=[], ema10=[], ema10_roc=[], 
                ema20=[], ema20_roc=[], ema30=[], ema30_roc=[]
            )
            macd_response = MACDData(
                dif=[], dif_roc=[], dea=[], dea_roc=[], macd=[], macd_roc=[]
            )
            ema_response = EMAData(ema12=[], ema26=[])
            
            return CoinAPIResponse(
                CoinData=CoinData(
                    dates=dates,
                    values=values,
                    ma=ma_response,
                    macd=macd_response,
                    ema=ema_response
                )
            )
        
        # 6. 处理合并后的数据
        # 使用字符串日期作为dates
        dates = merged_df['merge_key'].tolist()
        
        # 获取OHLCV数据
        values = []
        for _, row in merged_df.iterrows():
            values.append([
                nan_to_none(row['open']), 
                nan_to_none(row['close_kline']), 
                nan_to_none(row['low']), 
                nan_to_none(row['high']), 
                nan_to_none(row['volume'])
            ])
        
        # 创建MA响应数据
        ma_response_data = MAData(
            ema5=series_to_list(merged_df['ema5'] if 'ema5' in merged_df.columns else pd.Series([])),
            ema5_roc=series_to_list(merged_df['ema5_roc'] if 'ema5_roc' in merged_df.columns else pd.Series([])),
            ema10=series_to_list(merged_df['ema10'] if 'ema10' in merged_df.columns else pd.Series([])),
            ema10_roc=series_to_list(merged_df['ema10_roc'] if 'ema10_roc' in merged_df.columns else pd.Series([])),
            ema20=series_to_list(merged_df['ema20'] if 'ema20' in merged_df.columns else pd.Series([])),
            ema20_roc=series_to_list(merged_df['ema20_roc'] if 'ema20_roc' in merged_df.columns else pd.Series([])),
            ema30=series_to_list(merged_df['ema30'] if 'ema30' in merged_df.columns else pd.Series([])),
            ema30_roc=series_to_list(merged_df['ema30_roc'] if 'ema30_roc' in merged_df.columns else pd.Series([]))
        )
        
        macd_response_data = MACDData(
            dif=series_to_list(merged_df['dif'] if 'dif' in merged_df.columns else pd.Series([])),
            dif_roc=series_to_list(merged_df['dif_roc'] if 'dif_roc' in merged_df.columns else pd.Series([])),
            dea=series_to_list(merged_df['dea'] if 'dea' in merged_df.columns else pd.Series([])),
            dea_roc=series_to_list(merged_df['dea_roc'] if 'dea_roc' in merged_df.columns else pd.Series([])),
            macd=series_to_list(merged_df['macd'] if 'macd' in merged_df.columns else pd.Series([])),
            macd_roc=series_to_list(merged_df['macd_roc'] if 'macd_roc' in merged_df.columns else pd.Series([]))
        )
        
        ema_response_data = EMAData(
            ema12=series_to_list(merged_df['ema12'] if 'ema12' in merged_df.columns else pd.Series([])),
            ema26=series_to_list(merged_df['ema26'] if 'ema26' in merged_df.columns else pd.Series([]))
        )
        
        coin_data_response = CoinData(
            dates=dates,
            values=values,
            ma=ma_response_data,
            macd=macd_response_data,
            ema=ema_response_data
        )
        
        return CoinAPIResponse(CoinData=coin_data_response)

    except Exception as e:
        logger.error(f"为API获取K线数据时出错: {e}", exc_info=True)
        # 发生错误时返回空结构，确保API的健壮性
        return CoinAPIResponse( 
            CoinData=CoinData(
                dates=[],
                values=[],
                ma=MAData(ema5=[], ema5_roc=[], ema10=[], ema10_roc=[], ema20=[], ema20_roc=[], ema30=[], ema30_roc=[]),
                macd=MACDData(dif=[], dif_roc=[], dea=[], dea_roc=[], macd=[], macd_roc=[]),
                ema=EMAData(ema12=[], ema26=[])
            )
        )

# 如果您想直接运行此文件进行测试 (例如使用 uvicorn myfastapi.echarts:app --reload):
# 请确保 PYTHONPATH 设置正确，以便能够找到父目录中的 database.py 和 config.py
# 例如: export PYTHONPATH=/path/to/your/Cryp/AutoTradingBinance:$PYTHONPATH
# 或者在运行uvicorn的命令前加上PYTHONPATH的设置：
# PYTHONPATH=.. uvicorn myfastapi.echarts:app --reload --port 8001 (如果从myfastapi目录运行)

# 移除或注释掉旧的示例返回，因为我们已经实现了 get_kline_data_from_db
# 旧的 @app.get("/kline-ma-cd-data") 应该被上面的实现所取代。

# The uvicorn.run call should be in your main executable script (e.g., myfastapi/main.py)
# and not here if this file is meant to be a module providing a router.