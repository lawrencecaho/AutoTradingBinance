from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class KlineTable(Base):
    __tablename__ = 'kline_table'

    id = Column(String, primary_key=True)
    symbol = Column(String, index=True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    open_time = Column(DateTime)
    close_time = Column(DateTime)
    quote_asset_volume = Column(Float)
    num_trades = Column(Integer)
    taker_buy_base_vol = Column(Float)
    taker_buy_quote_vol = Column(Float)
    timestamp = Column(DateTime)  # 数据入库时间
