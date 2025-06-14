# config.py

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 测试用，实际使用需要从数据库获取
BINANCE_API_KEY = 'PqG0U5YaArRtRKFPzXXS3AWnBX817uSpYnMIluDkG0RyDVVcphhtUsvLgw46MtJH'
BINANCE_PRIVATE_KEY_PATH = 'Secret/Binance-testnet-prvke.pem'

SYMBOL = 'ETHUSDT'

StableUrl = 'https://api.binance.com/api/v3/'

# 数据库连接配置
DATABASE_URL = "postgresql+psycopg2://postgres:hejiaye%402006@192.168.1.20:5432/trading"

FETCH_INTERVAL_SECONDS = 6  # 价格获取间隔，单位为秒


def dbget_option(varb, cast_type):
    """
    查询 global_options 表中 varb 字段为 varb 的 options 字段值。
    如果没有对应的 varb，则返回 None。
    支持类型转换，默认返回 str，可指定 int、float 等。
    """
    from sqlalchemy import Table, MetaData, select
    from database import Session, engine

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
    from database import Session, engine

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
    from database import Session, engine

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




