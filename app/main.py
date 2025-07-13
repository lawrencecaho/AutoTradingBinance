# main.py
# 目前不具备完整的交易逻辑和API接口功能

import os
import sys
import time
import uvicorn
import asyncio
import logging
from pathlib import Path

# 添加当前目录到Python路径，确保可以导入其他模块
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from DatabaseOperator.pg_operator import init_db, Session
from ExchangeFetcher.fetcher import fetch_price, get_kline
from sqlalchemy import Table, MetaData

async def rollfetch_kline():
    '''
    异步获取K线数据并存储到数据库
    相关参数需要被定义在 redis 或主数据库
    运行时优先执行数据表离散度分析
    '''
    logging.info("开始异步获取据K线数,优先执行数据表离散度分析")


def main():
    #需要(symbol, interval, dbr=False, session=None, table=None,startTime=None, endTime=None, limit=100)
    metadata = MetaData()
    KLineTable = Table(
        "KLine_ETHUSDT",
        metadata,
        autoload_with=Session().get_bind()
    )
    session = Session()
    test = get_kline("ETHUSDT", "1m", dbr=True, session=session, table=KLineTable, startTime=None, endTime=None, limit=100)
    print(test)
    session.close()

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("myfastapi.main:app", host="0.0.0.0", port=8000, reload=True)
    main()
