"""
database.py
- 提供动态表创建和数据库初始化功能
"""
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from config import DATABASE_URL, SYMBOL
from DataModificationModule import KlineTable

Base = declarative_base()
metadata = MetaData()

def create_dynamic_table(base_name):
    """
    动态创建以 symbol 为后缀的表，id为字符串主键
    """
    return Table(
        f"{base_name}_{SYMBOL.lower()}",
        metadata,
        Column('id', String(16), primary_key=True),  # id 改为字符串
        Column('symbol', String),
        Column('price', Float),
        Column('timestamp', DateTime, default=lambda: datetime.now(timezone.utc))
    )

# 动态生成表
Price = create_dynamic_table("price_data")
PriceDiff = create_dynamic_table("price_diff") # 需要决断作用
BuyHistory = create_dynamic_table("buy_history")

# 初始化数据库连接
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_db():
    """
    初始化所有动态表结构
    """
    print(f"[Database] Initializing tables for symbol: {SYMBOL}")
    metadata.create_all(engine)

def generate_custom_id(session, table):
    # 重要部分
    """
    生成自定义主键id，格式为 yyyymmdd+8位十进制序号（字符串）
    Generate a custom ID based on the current date and an 8-digit sequence number
    Format: yyyymmdd + 8-digit sequence number
    重要部分
    """
    today_str = datetime.now(timezone.utc).strftime('%Y%m%d')
    result = session.execute(
        table.select()
        .where(table.c.id.like(f'{today_str}%'))
        .order_by(table.c.id.desc())
        .limit(1)
    ).first()
    if result:
        last_id = str(result.id)[8:]
        last_sn = int(last_id)
        new_sn = last_sn + 1
    else:
        new_sn = 1
    sn_str = f"{new_sn:08d}"
    return f"{today_str}{sn_str}"

def dbinsert_common(session, table, var, value, **kwargs):
    """
    插入表中指定字段的记录
    """
    custom_id = generate_custom_id(session, table)
    entry = table.insert().values(
        id=custom_id,
        **{var: value, **kwargs}
    )
    session.execute(entry)
    session.commit()
    return custom_id
def dbelete_common(session, table, var, value):
    """
    删除表中指定字段的记录
    """
    delete_entry = table.delete().where(table.c[var] == value)
    session.execute(delete_entry)
    session.commit()
    return True
def dbupdate_common(session, table, var, value, **kwargs):
    """
    更新表中指定字段的记录
    """
    update_entry = table.update().where(table.c[var] == value).values(**kwargs)
    session.execute(update_entry)
    session.commit()
    return True
def dbselect_common(session, table_name, var, value):
    """
    查询表中指定字段的记录
    Args:
        session: SQLAlchemy session
        table_name: 表名字符串
        var: 查询字段名
        value: 查询值
    Returns:
        list of tuples: 查询结果列表
    """
    # 从元数据中获取表对象
    table = Table(table_name, metadata, autoload_with=engine)
    select_entry = table.select().where(table.c[var] == value)
    result = session.execute(select_entry).fetchall()
    return result

def insert_price(session, Price, symbol, price, timestamp):
    """
    插入价格数据，id为自定义格式（字符串）
    """
    custom_id = generate_custom_id(session, Price)
    price_entry = Price.insert().values(
        id=custom_id,
        symbol=symbol,
        price=price,
        timestamp=timestamp
    )
    session.execute(price_entry)
    session.commit()
    return custom_id

# 存储K线数据
def insert_kline(session, table, symbol, kline):
    custom_id = generate_custom_id(session, table)
    kline_entry = table.insert().values(
        id=custom_id,
        symbol=symbol,
        open=float(kline['open']),
        high=float(kline['high']),
        low=float(kline['low']),
        close=float(kline['close']),
        volume=float(kline['volume']),
        open_time=datetime.fromtimestamp(kline['open_time'] / 1000, tz=timezone.utc),
        close_time=datetime.fromtimestamp(kline['close_time'] / 1000, tz=timezone.utc),
        quote_asset_volume=float(kline['quote_asset_volume']),
        num_trades=int(kline['num_trades']),
        taker_buy_base_vol=float(kline['taker_buy_base_vol']),
        taker_buy_quote_vol=float(kline['taker_buy_quote_vol']),
        timestamp=datetime.now(timezone.utc)
    )
    session.execute(kline_entry)
    session.commit()
    return custom_id

# 存储订单信息
def insert_order(session, table, symbol, side, price, quantity):
    """
    插入订单数据，id为自定义格式（字符串）
    有两个bool类型字段，分别表示订单是否完成和是否读取
    默认值为False
    """
    custom_id = generate_custom_id(session, table)
    order_entry = table.insert().values(
        id=custom_id,
        symbol=symbol,
        side=side,
        price=price,
        quantity=quantity,
        statusdone=False,
        statusreade=False,
        timestamp=datetime.now(timezone.utc)
    )
    session.execute(order_entry)
    session.commit()
    return custom_id