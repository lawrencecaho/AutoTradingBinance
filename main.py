# main.py

import time
from config import FETCH_INTERVAL_SECONDS
from database import init_db
from fetcher import fetch_price
from calculator import calculate_diff
from strategy import should_trade
from trader import execute_trade

def main():
    init_db()

    while True:
        print("\n[Main] Cycle Start")
        fetch_price()
        calculate_diff()
        decision = should_trade()
        execute_trade(decision)
        print("[Main] Cycle Complete\n")
        time.sleep(FETCH_INTERVAL_SECONDS)

if __name__ == '__main__':
    main()
