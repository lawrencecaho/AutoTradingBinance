# main.py
# 目前不具备完整的交易逻辑和API接口功能

import os
import sys
import time
import uvicorn
import asyncio
import logging
from pathlib import Path
from sqlalchemy import Table, MetaData

# 添加当前目录到Python路径，确保可以导入其他模块
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 导入内部组件
from config.logging_config import setup_logging, get_logger
from DatabaseOperator import *
from ExchangeFetcher import fetch_price, get_kline
from WorkLine import main as workline_main

async def QueueSettings():
    '''
    异步设置队列
    需要定义队列的名称和相关参数
    '''
    logging.info("开始设置Queue队列")


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
    # 设置统一的日志配置
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("应用程序启动")
    logging.info("启动主程序")


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("myfastapi.main:app", host="0.0.0.0", port=8000, reload=True)
    asyncio.run(main())
