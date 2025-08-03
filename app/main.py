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

from DatabaseOperator import init_db, Session
from ExchangeFetcher import fetch_price, get_kline
from sqlalchemy import Table, MetaData

async def kline_rollfetch():
    '''
    异步获取K线数据并存储到数据库
    相关参数需要被定义在 redis 与主数据库
    运行时优先执行数据表离散度分析
    '''
    logging.info("开始异步获取K线数据,优先执行数据表离散度分析")

async def FortunepointFounder():
    '''
    异步获取交易信号
    需要定义交易策略和信号生成逻辑
    '''
    logging.info("开始异步获取交易信号")

async def main():
    '''
    Production environment Entry Point
    '''
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("myfastapi.main:app", host="0.0.0.0", port=8000, reload=True)
    asyncio.run(main())
