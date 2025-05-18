# main.py

import time
from config import FETCH_INTERVAL_SECONDS
from database import init_db,Session
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
    session.close()

if __name__ == '__main__':
    main()
