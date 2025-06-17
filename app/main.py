# main.py
# 目前不具备完整的交易逻辑和API接口功能

import os
import sys
import time
import uvicorn
from pathlib import Path

# 添加当前目录到Python路径，确保可以导入其他模块
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from config import FETCH_INTERVAL_SECONDS
from database import init_db, Session
from fetcher import fetch_price, get_kline
from calculator import calculate_diff
from strategy import should_trade
from trader import execute_trade
from sqlalchemy import Table, MetaData

def main():
    """
    init_db()

    while True:
        print("\n[Main] Cycle Start")
        fetch_price()
        calculate_diff()
        decision = should_trade()
        execute_trade(decision)
        print("[Main] Cycle Complete\n")
        time.sleep(FETCH_INTERVAL_SECONDS)
    """
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
    #session.close()

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run("myfastapi.main:app", host="0.0.0.0", port=8000, reload=True)
    main()
