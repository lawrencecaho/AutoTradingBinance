# database.py

from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
from config import DATABASE_URL, SYMBOL

Base = declarative_base()

# 动态生成表名，基于 SYMBOL
class Price(Base):
    __tablename__ = f'price_data_{SYMBOL.lower()}'  # 表名包含币种符号
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# 差额表：记录买入与当前价格的差值
class PriceDiff(Base):
    __tablename__ = f'price_diff_{SYMBOL.lower()}'
    id = Column(Integer, primary_key=True)
    diff = Column(Float)
    current_price = Column(Float)
    buy_price = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# 买入记录表（简化版）
class BuyHistory(Base):
    __tablename__ = f'buy_history_{SYMBOL.lower()}'
    id = Column(Integer, primary_key=True)
    price = Column(Float)
    quantity = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# 初始化数据库连接
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# 修改 init_db 函数以支持动态表名
def init_db():
    print(f"[Database] Initializing table: {Price.__tablename__}")
    Base.metadata.create_all(engine)
