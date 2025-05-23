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

    """
    
    1499040000000,      // 开盘时间
    "0.01634790",       // 开盘价
    "0.80000000",       // 最高价
    "0.01575800",       // 最低价
    "0.01577100",       // 收盘价(当前K线未结束的即为最新价)
    "148976.11427815",  // 成交量
    1499644799999,      // 收盘时间
    "2434.19055334",    // 成交额
    308,                // 成交笔数
    "1756.87402397",    // 主动买入成交量
    "28.46694368",      // 主动买入成交额
    "17928899.62484339" // 请忽略该参数
    """

# 这里定义了K线数据的字段
# 这些字段与Binance API返回的K线数据字段一致
# 方便后续解析和存储
KLINE_FIELDS = [
    'open_time', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_asset_volume', 'num_trades',
    'taker_buy_base_vol', 'taker_buy_quote_vol', 'ignore'
]

def parse_kline(raw):
    return dict(zip(KLINE_FIELDS, raw))
    """
    解析原始K线数据为字典格式
    这里使用了zip函数将字段名和原始数据一一对应
    返回一个字典
    字典的键为字段名，值为原始数据
    """
