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
    create_engine, Column, Integer, Float, String, DateTime, Enum, Table, MetaData, asc, desc, inspect, DECIMAL, BigInteger, Text, VARCHAR, TIMESTAMP, text, func, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import sessionmaker
from sqlalchemy.event import listens_for
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
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
    
    # 初始化 Fetcher Queue 配置表
    InitializingFetcherQueueTable()
    
    logging.info("[Database] All tables initialized successfully.")

# 初始化 Binance 订单表 / Initialize Binance Order Table
def InitializingOrderTable():
    """
    初始化 Binance 订单表
    根据 Binance Spot WebSocket API order.place 参数规范创建
    """
    # 创建 PostgreSQL 数据表映射类
    class BinanceOrder(Base):
        __tablename__ = 'BinanceOrders'

        # 主键字段
        id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
        
        # 必填字段 - Binance API 要求
        symbol = Column(VARCHAR(20), nullable=False, index=True, comment='交易对，如 BTCUSDT')
        side = Column(Enum('BUY', 'SELL', name='order_side_enum'), nullable=False, comment='买卖方向')
        type = Column(Enum('LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 
                           'TAKE_PROFIT_LIMIT', 'LIMIT_MAKER', name='order_type_enum'), 
                     nullable=False, comment='订单类型')
        
        # 条件必填字段 - 根据订单类型决定是否必需
        timeInForce = Column(Enum('GTC', 'IOC', 'FOK', name='time_in_force_enum'), 
                            nullable=True, comment='有效期策略（LIMIT相关订单必需）')
        quantity = Column(DECIMAL(20, 8), nullable=True, comment='基础资产数量')
        quoteOrderQty = Column(DECIMAL(20, 8), nullable=True, comment='按计价资产金额下单（仅MARKET订单）')
        price = Column(DECIMAL(20, 8), nullable=True, comment='限价（LIMIT相关订单必需）')
        stopPrice = Column(DECIMAL(20, 8), nullable=True, comment='触发价（触发类订单必需）')
        trailingDelta = Column(BigInteger, nullable=True, comment='追踪止损步长（与stopPrice二选一）')
        
        # 可选字段
        icebergQty = Column(DECIMAL(20, 8), nullable=True, comment='冰山单外显数量')
        newClientOrderId = Column(VARCHAR(36), nullable=True, unique=True, comment='客户自定义订单ID')
        newOrderRespType = Column(Enum('ACK', 'RESULT', 'FULL', name='order_resp_type_enum'), 
                                 nullable=True, default='ACK', comment='返回内容级别')
        selfTradePreventionMode = Column(Enum('EXPIRE_TAKER', 'EXPIRE_MAKER', 'EXPIRE_BOTH', 
                                            name='self_trade_prevention_enum'), 
                                       nullable=True, comment='自成交防护模式')
        strategyId = Column(BigInteger, nullable=True, comment='策略标识')
        strategyType = Column(Integer, nullable=True, comment='策略类型')
        recvWindow = Column(BigInteger, nullable=True, comment='接收窗口时间')
        
        # 系统字段
        timestamp = Column(BigInteger, nullable=False, comment='请求时间戳（毫秒）')
        
        # 订单状态追踪字段
        order_id = Column(BigInteger, nullable=True, comment='交易所返回的订单ID')
        client_order_id = Column(VARCHAR(36), nullable=True, comment='实际使用的客户端订单ID')
        order_status = Column(Enum('NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELED', 'PENDING_CANCEL', 
                                  'REJECTED', 'EXPIRED', name='order_status_enum'), 
                             nullable=True, comment='订单状态')
        executed_qty = Column(DECIMAL(20, 8), nullable=True, default=0, comment='已成交数量')
        cummulative_quote_qty = Column(DECIMAL(20, 8), nullable=True, default=0, comment='累计成交金额')
        
        # 系统管理字段
        is_test_order = Column(Boolean, nullable=False, default=False, comment='是否为测试订单')
        error_code = Column(Integer, nullable=True, comment='错误代码（如果有）')
        error_msg = Column(Text, nullable=True, comment='错误信息（如果有）')
        
        # 时间戳字段
        created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), comment='记录创建时间')
        updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), 
                           onupdate=func.now(), comment='记录更新时间')
        order_time = Column(TIMESTAMP(timezone=True), nullable=True, comment='订单时间（交易所时间）')
        
        # 创建索引
        __table_args__ = (
            # 复合索引用于查询优化
            {'comment': 'Binance 订单表，存储所有订单请求和响应数据'}
        )
    
    Base.metadata.create_all(engine)
    logging.info("[Database] Order table initialized successfully with full Binance API compliance.")

def InitializingFetcherQueueTable():
    """
    初始化数据获取队列配置表
    """
    # 创建队列配置数据表映射类
    class FetcherQueueConfig(Base):
        """
        数据获取队列配置表
        PostgreSQL 表设置
        """
        __tablename__ = 'fetcher_queue_configs'

        id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
        queue_name = Column(VARCHAR(255), unique=True, nullable=False)  # 队列名称，唯一
        symbol = Column(VARCHAR(50), nullable=False)  # 交易对符号，如 BTCUSDT
        exchange = Column(VARCHAR(50), nullable=False, default='binance')  # 交易所名称，默认 binance
        interval = Column(VARCHAR(10), nullable=False)  # K线周期，如 1m, 5m, 1h, 1d
        is_active = Column(Boolean, nullable=False, default=False)  # 是否激活，默认不激活
        description = Column(Text, nullable=True)  # 队列描述
        created_by = Column(VARCHAR(255), nullable=False)  # 创建者用户ID/用户名
        updated_by = Column(VARCHAR(255), nullable=True)  # 最后更新者用户ID/用户名
        created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
        updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    Base.metadata.create_all(engine)
    logging.info("[Database] Fetcher queue config table initialized successfully.")

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
    
    # 准备数据
    kline_data = {
        'symbol': symbol,
        'open': float(kline['open']),
        'high': float(kline['high']),
        'low': float(kline['low']),
        'close': float(kline['close']),
        'volume': float(kline['volume']),
        'open_time': open_time,
        'close_time': close_time,
        'quote_asset_volume': float(kline['quote_asset_volume']),
        'num_trades': int(kline['num_trades']),
        'taker_buy_base_vol': float(kline['taker_buy_base_vol']),
        'taker_buy_quote_vol': float(kline['taker_buy_quote_vol']),
        'timestamp': datetime.now(timezone.utc)
    }
    
    try:
        # 使用 PostgreSQL 的 ON CONFLICT DO UPDATE 语法进行 UPSERT
        from sqlalchemy.dialects.postgresql import insert
        
        stmt = insert(table).values(**kline_data)
        # 如果主键冲突，则更新除主键外的所有字段
        update_dict = {key: stmt.excluded[key] for key in kline_data.keys() if key != 'open_time'}
        stmt = stmt.on_conflict_do_update(
            index_elements=['open_time'],
            set_=update_dict
        )
        
        session.execute(stmt)
        # 注意：不在这里commit，让上下文管理器处理
        print(f"[Database] UPSERT K线数据成功: {symbol} {open_time}")
        return open_time
        
    except Exception as e:
        logging.error(f"UPSERT K线数据失败: {e}", exc_info=True)
        # 不在这里rollback，让上下文管理器处理
        return None

class ExchangeDataFetcherQueueSettings:
    """
    交易所数据获取队列配置管理器
    用于管理存储在 PostgreSQL 中的队列配置
    """
    
    def __init__(self):
        self.engine = engine
        self.Session = Session
    
    def create_queue_config(self, queue_name: str, symbol: str, interval: str, 
                          exchange: str = 'binance', description: Optional[str] = None, 
                          created_by: str = 'system') -> bool:
        """
        创建新的队列配置
        
        Args:
            queue_name: 队列名称（唯一）
            symbol: 交易对符号，如 BTCUSDT
            interval: K线周期，如 1m, 5m, 1h, 1d
            exchange: 交易所名称，默认 binance
            description: 队列描述
            created_by: 创建者用户ID/用户名，默认 'system'
        
        Returns:
            bool: 创建成功返回 True，失败返回 False
        """
        session = self.Session()
        try:
            from sqlalchemy import Table, MetaData, insert
            
            metadata = MetaData()
            queue_table = Table('fetcher_queue_configs', metadata, autoload_with=self.engine)
            
            stmt = insert(queue_table).values(
                queue_name=queue_name,
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                is_active=False,  # 默认创建为不激活状态
                description=description,
                created_by=created_by
            )
            
            session.execute(stmt)
            session.commit()
            logging.info(f"[QueueConfig] 创建队列配置成功: {queue_name}")
            return True
            
        except Exception as e:
            logging.error(f"[QueueConfig] 创建队列配置失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_queue_config(self, queue_name: str) -> Optional[Dict]:
        """
        获取指定队列的配置
        
        Args:
            queue_name: 队列名称
        
        Returns:
            Optional[Dict]: 队列配置字典，不存在则返回 None
        """
        session = self.Session()
        try:
            from sqlalchemy import Table, MetaData, select
            
            metadata = MetaData()
            queue_table = Table('fetcher_queue_configs', metadata, autoload_with=self.engine)
            
            stmt = select(queue_table).where(queue_table.c.queue_name == queue_name)
            result = session.execute(stmt).first()
            
            if result:
                return {
                    'id': str(result.id),
                    'queue_name': result.queue_name,
                    'symbol': result.symbol,
                    'exchange': result.exchange,
                    'interval': result.interval,
                    'is_active': result.is_active,
                    'description': result.description,
                    'created_by': result.created_by,
                    'updated_by': result.updated_by,
                    'created_at': result.created_at.isoformat() if result.created_at else None,
                    'updated_at': result.updated_at.isoformat() if result.updated_at else None
                }
            return None
            
        except Exception as e:
            logging.error(f"[QueueConfig] 获取队列配置失败: {e}")
            return None
        finally:
            session.close()
    
    def get_all_queue_configs(self, active_only: bool = True) -> List[Dict]:
        """
        获取所有队列配置
        
        Args:
            active_only: 是否只返回激活的队列配置
        
        Returns:
            List[Dict]: 队列配置列表
        """
        session = self.Session()
        try:
            from sqlalchemy import Table, MetaData, select
            
            metadata = MetaData()
            queue_table = Table('fetcher_queue_configs', metadata, autoload_with=self.engine)
            
            stmt = select(queue_table)
            if active_only:
                stmt = stmt.where(queue_table.c.is_active == True)
            
            results = session.execute(stmt).fetchall()
            
            configs = []
            for result in results:
                configs.append({
                    'id': str(result.id),
                    'queue_name': result.queue_name,
                    'symbol': result.symbol,
                    'exchange': result.exchange,
                    'interval': result.interval,
                    'is_active': result.is_active,
                    'description': result.description,
                    'created_by': result.created_by,
                    'updated_by': result.updated_by,
                    'created_at': result.created_at.isoformat() if result.created_at else None,
                    'updated_at': result.updated_at.isoformat() if result.updated_at else None
                })
            
            return configs
            
        except Exception as e:
            logging.error(f"[QueueConfig] 获取所有队列配置失败: {e}")
            return []
        finally:
            session.close()
    
    def update_queue_config(self, queue_name: str, updated_by: str = 'system', **kwargs) -> bool:
        """
        更新队列配置
        
        Args:
            queue_name: 队列名称
            updated_by: 更新者用户ID/用户名，默认 'system'
            **kwargs: 要更新的字段
        
        Returns:
            bool: 更新成功返回 True，失败返回 False
        """
        session = self.Session()
        try:
            from sqlalchemy import Table, MetaData, update
            
            metadata = MetaData()
            queue_table = Table('fetcher_queue_configs', metadata, autoload_with=self.engine)
            
            # 过滤掉不允许更新的字段
            allowed_fields = ['symbol', 'exchange', 'interval', 'is_active', 'description']
            update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            # 添加更新者信息
            update_data['updated_by'] = updated_by
            
            if len(update_data) <= 1:  # 只有 updated_by 字段
                logging.warning(f"[QueueConfig] 没有有效的更新字段")
                return False
            
            stmt = update(queue_table).where(queue_table.c.queue_name == queue_name).values(**update_data)
            result = session.execute(stmt)
            session.commit()
            
            if result.rowcount > 0:
                logging.info(f"[QueueConfig] 更新队列配置成功: {queue_name}")
                return True
            else:
                logging.warning(f"[QueueConfig] 队列配置不存在: {queue_name}")
                return False
                
        except Exception as e:
            logging.error(f"[QueueConfig] 更新队列配置失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def delete_queue_config(self, queue_name: str) -> bool:
        """
        删除队列配置
        
        Args:
            queue_name: 队列名称
        
        Returns:
            bool: 删除成功返回 True，失败返回 False
        """
        session = self.Session()
        try:
            from sqlalchemy import Table, MetaData, delete
            
            metadata = MetaData()
            queue_table = Table('fetcher_queue_configs', metadata, autoload_with=self.engine)
            
            stmt = delete(queue_table).where(queue_table.c.queue_name == queue_name)
            result = session.execute(stmt)
            session.commit()
            
            if result.rowcount > 0:
                logging.info(f"[QueueConfig] 删除队列配置成功: {queue_name}")
                return True
            else:
                logging.warning(f"[QueueConfig] 队列配置不存在: {queue_name}")
                return False
                
        except Exception as e:
            logging.error(f"[QueueConfig] 删除队列配置失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def activate_queue(self, queue_name: str, updated_by: str = 'system') -> bool:
        """激活队列"""
        return self.update_queue_config(queue_name, updated_by=updated_by, is_active=True)
    
    def deactivate_queue(self, queue_name: str, updated_by: str = 'system') -> bool:
        """停用队列"""
        return self.update_queue_config(queue_name, updated_by=updated_by, is_active=False)

# 创建全局实例
fetcher_queue_manager = ExchangeDataFetcherQueueSettings()

# 存储订单信息
def insert_order_Binance(session, table, order_data):
    """
    插入订单数据，支持完整的 Binance API 字段
    
    Args:
        session: SQLAlchemy session
        table: 订单表对象
        order_data: 包含订单数据的字典，支持以下字段：
            必填: symbol, side, type, timestamp
            条件必填: timeInForce, quantity, quoteOrderQty, price, stopPrice, trailingDelta
            可选: icebergQty, newClientOrderId, newOrderRespType, selfTradePreventionMode,
                  strategyId, strategyType, recvWindow, is_test_order 等
    
    Returns:
        str: 生成的订单UUID
    """
    from sqlalchemy.dialects.postgresql import insert
    
    # 设置默认值
    order_entry_data = {
        'symbol': order_data.get('symbol'),
        'side': order_data.get('side'),
        'type': order_data.get('type'),
        'timeInForce': order_data.get('timeInForce'),
        'quantity': order_data.get('quantity'),
        'quoteOrderQty': order_data.get('quoteOrderQty'),
        'price': order_data.get('price'),
        'stopPrice': order_data.get('stopPrice'),
        'trailingDelta': order_data.get('trailingDelta'),
        'icebergQty': order_data.get('icebergQty'),
        'newClientOrderId': order_data.get('newClientOrderId'),
        'newOrderRespType': order_data.get('newOrderRespType', 'ACK'),
        'selfTradePreventionMode': order_data.get('selfTradePreventionMode'),
        'strategyId': order_data.get('strategyId'),
        'strategyType': order_data.get('strategyType'),
        'recvWindow': order_data.get('recvWindow'),
        'timestamp': order_data.get('timestamp', int(datetime.now(timezone.utc).timestamp() * 1000)),
        'order_id': order_data.get('order_id'),
        'client_order_id': order_data.get('client_order_id'),
        'order_status': order_data.get('order_status', 'NEW'),
        'executed_qty': order_data.get('executed_qty', 0),
        'cummulative_quote_qty': order_data.get('cummulative_quote_qty', 0),
        'is_test_order': order_data.get('is_test_order', False),
        'error_code': order_data.get('error_code'),
        'error_msg': order_data.get('error_msg'),
        'order_time': order_data.get('order_time')
    }
    
    # 移除 None 值
    order_entry_data = {k: v for k, v in order_entry_data.items() if v is not None}
    
    try:
        # 使用 PostgreSQL 的 ON CONFLICT DO UPDATE 语法进行 UPSERT（如果需要）
        stmt = insert(table).values(**order_entry_data)
        
        # 如果有客户端订单ID冲突，则更新记录
        if 'newClientOrderId' in order_entry_data and order_entry_data['newClientOrderId']:
            update_dict = {key: stmt.excluded[key] for key in order_entry_data.keys() 
                          if key not in ['id', 'created_at']}
            stmt = stmt.on_conflict_do_update(
                index_elements=['newClientOrderId'],
                set_=update_dict
            )
        
        result = session.execute(stmt)
        session.commit()
        
        # 获取插入的记录ID
        if hasattr(result, 'inserted_primary_key') and result.inserted_primary_key:
            order_id = result.inserted_primary_key[0]
        else:
            # 如果是更新操作，通过客户端订单ID查询
            if 'newClientOrderId' in order_entry_data:
                from sqlalchemy import select
                stmt = select(table.c.id).where(table.c.newClientOrderId == order_entry_data['newClientOrderId'])
                order_id = session.execute(stmt).scalar()
            else:
                order_id = None
        
        logging.info(f"[Database] 订单数据插入/更新成功: {order_entry_data.get('symbol')} - {order_entry_data.get('side')}")
        return str(order_id) if order_id else None
        
    except Exception as e:
        logging.error(f"[Database] 订单数据插入失败: {e}", exc_info=True)
        session.rollback()
        return None

def change_order_Binance(session, table, order_id, update_data):
    """
    更新订单数据，支持完整的 Binance API 字段

    Args:
        session: SQLAlchemy session
        table: 订单表对象
        order_id: 订单ID
        update_data: 包含更新数据的字典，支持以下字段：
            可选: symbol, side, type, timestamp
            条件可选: timeInForce, quantity, quoteOrderQty, price, stopPrice, trailingDelta
            可选: icebergQty, newClientOrderId, newOrderRespType, selfTradePreventionMode,
                  strategyId, strategyType, recvWindow, is_test_order 等

    Returns:
        bool: 更新是否成功
    """
    try:
        stmt = table.update().where(table.c.id == order_id).values(**update_data)
        session.execute(stmt)
        session.commit()
        logging.info(f"[Database] 订单数据更新成功: {order_id}")
        return True
    except Exception as e:
        logging.error(f"[Database] 订单数据更新失败: {e}", exc_info=True)
        session.rollback()
        return False