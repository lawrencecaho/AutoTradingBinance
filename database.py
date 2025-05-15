# database.py

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from config import DATABASE_URL, SYMBOL

Base = declarative_base()
metadata = MetaData()

def create_dynamic_table(base_name):
    return Table(
        f"{base_name}_{SYMBOL.lower()}",
        metadata,
        Column('id', Integer, primary_key=True),
        Column('symbol', String),
        Column('price', Float),
        Column('timestamp', DateTime, default=lambda: datetime.now(timezone.utc))
    )

# 动态生成表
Price = create_dynamic_table("price_data")
PriceDiff = create_dynamic_table("price_diff")
BuyHistory = create_dynamic_table("buy_history")

# 初始化数据库连接
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# 修改 init_db 函数以支持动态表名
def init_db():
    print(f"[Database] Initializing tables for symbol: {SYMBOL}")
    metadata.create_all(engine)
