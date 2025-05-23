"""
database.py
- 提供动态表创建和数据库初始化功能
"""
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Table, MetaData, asc, desc # Added asc, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from config import DATABASE_URL, SYMBOL
from DataModificationModule import KlineTable
import logging # Ensure logging is imported at the module level

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
def dbdelete_common(session, table, var, value):
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
    查询指定表中指定字段的记录
    Args:
        session: SQLAlchemy session
        table_name: 表名字符串
        var: 查询字段名
        value: 查询值类型
    Returns:
        list of tuples: 查询结果列表
    """
    # 从元数据中获取表对象
    table = Table(table_name, metadata, autoload_with=engine)
    select_entry = table.select().where(table.c[var] == value)
    result = session.execute(select_entry).fetchall()
    return result

def dbget_kline(session, table_name: str, symbol_value: str, order_by_column: Optional[str] = 'open_time', ascending: bool = True):
    """
    查询指定K线表中特定交易对的数据，并可选择排序.
    Args:
        session: SQLAlchemy session
        table_name: K线表名字符串 (e.g., "KLine_BTCUSDT")
        symbol_value: 交易对的值 (e.g., "BTCUSDT")
        order_by_column: 用于排序的列名。默认为 "open_time".
                         如果为 None，则不进行特定排序 (依赖数据库默认)。
        ascending: True for ascending order, False for descending. 默认为 True.
    Returns:
        list of tuples: 查询结果列表, 或在表/列不存在时返回空列表并记录错误。
    """
    try:
        table = Table(table_name, metadata, autoload_with=engine)

        if 'symbol' not in table.c:
            logging.error(f"列 'symbol' 在表 '{table_name}' 中未找到。")
            return []
        if order_by_column and order_by_column not in table.c:
            logging.warning(f"排序列 '{order_by_column}' 在表 '{table_name}' 中未找到。将不进行排序。")
            order_by_column = None 

        query = table.select().where(table.c.symbol == symbol_value)
        
        if order_by_column:
            order_direction = asc if ascending else desc
            query = query.order_by(order_direction(table.c[order_by_column]))
            
        result = session.execute(query).fetchall()
        return result
    except Exception as e:
        logging.error(f"查询表 '{table_name}' 时发生错误: {e}", exc_info=True)
        return []

def Time_Discrete_Check(table_name: str, time_column_name: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None, days_ago: Optional[int] = None) -> List[datetime]:
    """
    获取数据表中指定时间列在给定日期范围内的时间数据。
    函数内部处理数据库会话的创建和关闭。

    可以通过两种方式指定时间范围：
    1. start_time 和 end_time: 提供两个精确的 datetime 对象确定范围。
       两个时间都必须提供，并且应该是时区感知的 (timezone-aware)。
    2. days_ago: 提供一个整数，代表从当前时间回溯的天数。

    Args:
        table_name: 要查询的表名。
        time_column_name: 存储时间的列名。
        start_time: 范围的开始时间 (datetime object, timezone-aware)。
        end_time: 范围的结束时间 (datetime object, timezone-aware)。
        days_ago: 从当前时间回溯的天数 (integer)。

    Returns:
        List[datetime]: 包含查询到的时间值 (datetime objects) 的列表。

    Raises:
        ValueError: 如果时间范围参数提供不正确或不一致，或者列名无效。
    """
    session = Session()  # 创建一个新的会话
    try:
        table = Table(table_name, metadata, autoload_with=engine)

        # 检查时间列是否存在
        if time_column_name not in table.c:
            raise ValueError(f"列 '{time_column_name}' 在表 '{table_name}' 中未找到。")

        actual_start_time: datetime
        actual_end_time: datetime

        if days_ago is not None:
            if start_time is not None or end_time is not None:
                raise ValueError("不能同时指定 days_ago 和 start_time/end_time。")
            if not isinstance(days_ago, int) or days_ago <= 0:
                raise ValueError("days_ago 必须是一个正整数。")
            
            actual_end_time = datetime.now(timezone.utc)
            actual_start_time = actual_end_time - timedelta(days=days_ago)
        
        elif start_time is not None and end_time is not None:
            if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
                raise ValueError("start_time 和 end_time 必须是 datetime 对象。")
            if start_time.tzinfo is None or end_time.tzinfo is None:
                raise ValueError("start_time 和 end_time 必须是时区感知的 datetime 对象。")
            if start_time > end_time:
                raise ValueError("start_time 不能晚于 end_time。")

            actual_start_time = start_time
            actual_end_time = end_time
        else:
            raise ValueError("必须指定 'days_ago' 或同时指定 'start_time' 和 'end_time'。")

        query = table.select().with_only_columns(table.c[time_column_name]).where(
            table.c[time_column_name].between(actual_start_time, actual_end_time)
        ).order_by(table.c[time_column_name])

        result_proxy = session.execute(query)
        time_values = [row[0] for row in result_proxy.fetchall()]
        
        return time_values

    finally:
        session.close()  # 确保会话被关闭

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