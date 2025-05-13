# config.py

BINANCE_API_KEY = 'your_binance_api_key'
BINANCE_SECRET_KEY = 'your_secret_key'
SYMBOL = 'ETHUSDT'

DATABASE_URL = 'sqlite:///crypto.db'  # 使用 SQLite，部署时可换为 MySQL/PostgreSQL

FETCH_INTERVAL_SECONDS = 2 # 价格获取间隔，单位为秒
