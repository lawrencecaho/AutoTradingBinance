# app/DatabaseOperator/pg_operator.py
"""
pg_operator.py
- 负责与 PostgreSQL 数据库进行交互
- 提供基本的数据库操作函数
- 提供动态表创建和数据库初始化功能
"""
import os
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, Integer, Float, String, DateTime, Enum, Table, MetaData, asc, desc, inspect, DECIMAL, BigInteger, Text, VARCHAR, TIMESTAMP, text, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listens_for
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from DataProcessingCalculator.DataModificationModule import KlineTable
import logging # Ensure logging is imported at the module level

# 加载环境变量
load_dotenv()

# 从环境变量读取数据库连接URL
def get_database_url():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logging.error("DATABASE_URL 环境变量未设置，终止程序。")
        raise RuntimeError("DATABASE_URL 环境变量未设置，无法初始化数据库连接。")
    
    logging.info(f"使用环境变量中的数据库连接")
    return database_url

# 获取数据库URL
DATABASE_URL = get_database_url()

# 配置现在完全通过环境变量或参数传递，不再从config导入

Base = declarative_base()
metadata = MetaData()


# 初始化数据库连接
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def InitialBasicTable():
# 定义 global_options 表
    class GlobalOptions(Base):
        __tablename__ = 'global_options'

        id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
        varb = Column(Text, nullable=True)
        options = Column(VARCHAR(2048), nullable=True)
        reserve = Column(VARCHAR(2048), nullable=True)
        reserve1 = Column(Text, nullable=True)
        fixed_time = Column(TIMESTAMP, nullable=True)

    # 定义 userbasic 表
    class UserBasic(Base):
        __tablename__ = 'userbasic'

        uuid = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
        uid = Column(VARCHAR(255), unique=True, nullable=False)
        username = Column(VARCHAR(255), unique=True, nullable=False)
        totpsecret = Column(VARCHAR(255), nullable=False)
        created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
        updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # 为 global_options 表的 fixed_time 字段创建触发器逻辑
    @listens_for(GlobalOptions, "before_update")
    def update_fixed_time(mapper, connection, target):
        """
        在更新 global_options 表时，自动更新 fixed_time 字段
        """
        target.fixed_time = func.now()
    # 创建所有表
    Base.metadata.create_all(engine)
    logging.info("[Database] Basic tables initialized successfully.")

def init_db():
    """
    初始化数据库，创建必要的表
    """
    Base.metadata.create_all(engine)
    logging.info("[Database] Database initialized successfully.")
    
    # 初始化 Order 数据表
    InitializingOrderTable()
    
    logging.info("[Database] All tables initialized successfully.")

def InitializingOrderTable():
    """
    初始化 Order 数据表
    """
    # 创建 PostgreSQL 数据表映射类
    class Order(Base):
        __tablename__ = 'orders'

        symbol = Column(String, nullable=False)  # 字段类型: STRING, 必需
        side = Column(Enum('BUY', 'SELL', name='order_side_enum'), nullable=False)  # 字段类型: ENUM, 必需
        type = Column(Enum('LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 
                           'TAKE_PROFIT_LIMIT', name='order_type_enum'), nullable=False)  # 字段类型: ENUM, 必需
        timeInForce = Column(Enum('GTC', 'IOC', 'FOK', name='time_in_force_enum'), nullable=True)  # 字段类型: ENUM, 非必需
        quantity = Column(DECIMAL, nullable=True)  # 字段类型: DECIMAL, 非必需
        quoteOrderQty = Column(DECIMAL, nullable=True)  # 字段类型: DECIMAL, 非必需
        price = Column(DECIMAL, nullable=True)  # 字段类型: DECIMAL, 非必需
        newClientOrderId = Column(String, nullable=True)  # 字段类型: STRING, 非必需
        strategyId = Column(BigInteger, nullable=True)  # 字段类型: LONG, 非必需
        strategyType = Column(Integer, nullable=True)  # 字段类型: INT, 非必需
        stopPrice = Column(DECIMAL, nullable=True)  # 字段类型: DECIMAL, 非必需
        trailingDelta = Column(BigInteger, nullable=True)  # 字段类型: LONG, 非必需
        icebergQty = Column(DECIMAL, nullable=True)  # 字段类型: DECIMAL, 非必需
        newOrderRespType = Column(Enum('ACK', 'RESULT', 'FULL', name='order_resp_type_enum'), nullable=True)  # 字段类型: ENUM, 非必需
        selfTradePreventionMode = Column(Enum('STP', name='self_trade_prevention_enum'), nullable=True)  # 字段类型: ENUM, 非必需
        recvWindow = Column(BigInteger, nullable=True)  # 字段类型: LONG, 非必需
        timestamp = Column(BigInteger, nullable=False)  # 字段类型: LONG, 必需
    Base.metadata.create_all(engine)
    logging.info("[Database] Order table initialized successfully.")

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

def dbget_option(varb, cast_type):
    """
    查询 global_options 表中 varb 字段为 varb 的 options 字段值。
    如果没有对应的 varb，则返回 None。
    支持类型转换，默认返回 str，可指定 int、float 等。
    """
    from sqlalchemy import Table, MetaData, select

    metadata = MetaData()
    GlobalOption = Table("global_options", metadata, autoload_with=engine)
    session = Session()
    try:
        stmt = select(GlobalOption.c.options).where(GlobalOption.c.varb == varb)
        result = session.execute(stmt).scalar()
        if result is None:
            return None
        try:
            return cast_type(result)
        except Exception:
            print(f"[db_option] 类型转换失败: {result} -> {cast_type}")
            return result
    except Exception as e:
        print(f"[db_option] 查询出错: {e}")
        return None
    finally:
        session.close()


def dbinsert_option(varb, options):
    """
    插入或更新 global_options 表中的 varb 和 options 字段。
    如果 varb 已存在，则更新 options 字段。
    如果 varb 不存在，则插入新记录。
    """
    from sqlalchemy import Table, MetaData, insert, update, select

    metadata = MetaData()
    GlobalOption = Table('global_options', metadata, autoload_with=engine)
    session = Session()
    try:
        stmt = select(GlobalOption).where(GlobalOption.c.varb == varb)
        result = session.execute(stmt).first()
        if result:
            # 更新操作
            stmt = update(GlobalOption).where(GlobalOption.c.varb == varb).values(options=options)
            session.execute(stmt)
            print(f"[db_option] 更新 {varb} 的选项为 {options}")
        else:
            # 插入操作
            stmt = insert(GlobalOption).values(varb=varb, options=options)
            session.execute(stmt)
            print(f"[db_option] 插入 {varb} 的选项为 {options}")
        session.commit()
    except Exception as e:
        print(f"[db_option] 插入或更新出错: {e}")
        session.rollback()
    finally:
        session.close()


def dbdelete_option(varb):
    """
    删除 global_options 表中 varb 字段为 varb 的记录。
    """
    from sqlalchemy import Table, MetaData, delete

    metadata = MetaData()
    GlobalOption = Table("global_options", metadata, autoload_with=engine)
    session = Session()
    try:
        stmt = delete(GlobalOption).where(GlobalOption.c.varb == varb)
        session.execute(stmt)
        session.commit()
        print(f"[db_option] 删除 {varb} 的选项")
    except Exception as e:
        print(f"[db_option] 删除出错: {e}")
        session.rollback()
    finally:
        session.close()

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

def create_kline_table_if_not_exists(engine, symbol_value):
    """
    创建K线数据表如果不存在
    表名格式为 KLine_SYMBOLVALUE (例如 KLine_BTCUSDT)
    主键为自定义id，并保持与insert_kline函数相同的字段结构
    
    Args:
        engine: SQLAlchemy engine
        symbol_value: 交易对的值 (e.g., "BTCUSDT")
        
    Returns:
        Table: 创建或获取的表对象
    """
    metadata_obj = MetaData()
    inspector = inspect(engine)
    table_name = f"KLine_{symbol_value}"
    
    if inspector.has_table(table_name):
        # 如果表已存在，返回它
        return Table(table_name, metadata_obj, autoload_with=engine)
    
    # 定义表结构，与insert_kline函数相匹配
    kline_table = Table(
        table_name,
        metadata_obj,
        Column('symbol', String, index=True),
        Column('open', Float),
        Column('high', Float),
        Column('low', Float),
        Column('close', Float),
        Column('volume', Float),
        Column('open_time', DateTime(timezone=True), primary_key=True),  # 使用带时区的DateTime作为主键
        Column('close_time', DateTime(timezone=True)),  # 使用带时区的DateTime
        Column('quote_asset_volume', Float),
        Column('num_trades', Integer),
        Column('taker_buy_base_vol', Float),
        Column('taker_buy_quote_vol', Float),
        Column('timestamp', DateTime(timezone=True))  # 使用带时区的DateTime
    )
    
    logging.info(f"创建K线表: {table_name}")
    kline_table.create(engine)
    return kline_table

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
    # 将时间戳转换为datetime对象，UTC时区
    open_time = datetime.fromtimestamp(kline['open_time'] / 1000, tz=timezone.utc)
    close_time = datetime.fromtimestamp(kline['close_time'] / 1000, tz=timezone.utc)
    
    kline_entry = table.insert().values(
        symbol=symbol,
        open=float(kline['open']),
        high=float(kline['high']),
        low=float(kline['low']),
        close=float(kline['close']),
        volume=float(kline['volume']),
        open_time=open_time,  # 使用转换后的datetime对象
        close_time=close_time,  # 使用转换后的datetime对象
        quote_asset_volume=float(kline['quote_asset_volume']),
        num_trades=int(kline['num_trades']),
        taker_buy_base_vol=float(kline['taker_buy_base_vol']),
        taker_buy_quote_vol=float(kline['taker_buy_quote_vol']),
        timestamp=datetime.now(timezone.utc)
    )
    
    try:
        session.execute(kline_entry)
        session.commit()
        return open_time  # 返回datetime对象作为主键
    except Exception as e:
        session.rollback()
        logging.error(f"插入K线数据失败: {e}", exc_info=True)
        # 如果是主键冲突错误，可以考虑实现upsert逻辑或者忽略
        # 此处简单返回None表示插入失败
        return None

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