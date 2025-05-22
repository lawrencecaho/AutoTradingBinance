# config.py

from urllib.parse import quote_plus
import os
import secrets
import base64
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 测试用，实际使用需要从数据库获取
BINANCE_API_KEY = 'PqG0U5YaArRtRKFPzXXS3AWnBX817uSpYnMIluDkG0RyDVVcphhtUsvLgw46MtJH'
BINANCE_PRIVATE_KEY_PATH = 'Secret/Binance-testnet-prvke.pem'

SYMBOL = 'ETHUSDT'

StableUrl = 'https://api.binance.com/api/v3/'

# DATABASE_URL = 'postgresql://postgres:hejiaye%402006@192.168.1.20:5432/trading'  # 使用 SQLite，部署时可换为 MySQL/PostgreSQL

# URL encode password
password = quote_plus("hejiaye@2006")

# 构造连接字符串
# DATABASE_URL = f"postgresql+psycopg2://postgres:{password}@192.168.1.20:5432/trading"

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


def generate_api_secret_key(length: int = 32) -> bytes:
    """生成一个安全的 API 密钥"""
    return secrets.token_bytes(length)


def generate_jwt_secret(length: int = 64) -> str:
    """生成 JWT 密钥"""
    return secrets.token_urlsafe(length)


def save_api_keys(secret_dir: str = "Secret") -> dict:
    """生成并保存 API 密钥并更新环境变量"""
    # 确保 Secret 目录存在
    secret_path = Path(secret_dir)
    secret_path.mkdir(exist_ok=True)

    # 生成新的密钥
    api_secret = generate_api_secret_key()
    encryption_key = base64.urlsafe_b64encode(generate_api_secret_key()).decode()
    jwt_secret = generate_jwt_secret()

    # 更新环境变量文件
    env_path = Path(".env")
    env_content = f"""# JWT配置（仅后端使用）
JWT_SECRET={jwt_secret}

# 加密密钥（前后端共享）
ENCRYPTION_KEY={encryption_key}  # 需要与前端 NEXT_PUBLIC_ENCRYPT_KEY 一致
NEXT_PUBLIC_ENCRYPT_KEY={encryption_key}  # 与后端 ENCRYPTION_KEY 相同

# API密钥（仅后端使用）
API_SECRET_KEY={api_secret.hex()}
"""
    env_path.write_text(env_content)

    # 同时保存到 Secret 目录（作为备份）
    with open(secret_path / "api_secret.key", "wb") as f:
        f.write(api_secret)

    with open(secret_path / "encryption.key", "w") as f:
        f.write(encryption_key)

    with open(secret_path / "jwt_secret.key", "w") as f:
        f.write(jwt_secret)

    return {
        "api_secret": api_secret,
        "encryption_key": encryption_key.encode(),
        "jwt_secret": jwt_secret
    }


def load_api_keys(secret_dir: str = "Secret") -> dict:
    """加载 API 密钥，优先从环境变量加载"""
    # 首先尝试从环境变量加载
    jwt_secret = os.getenv("JWT_SECRET")
    encryption_key = os.getenv("ENCRYPTION_KEY")
    
    if jwt_secret and encryption_key:
        # 如果环境变量存在，使用环境变量的值
        encryption_key_bytes = base64.urlsafe_b64encode(encryption_key.encode())
        return {
            "api_secret": generate_api_secret_key(),  # API secret 总是随机生成
            "encryption_key": encryption_key_bytes,
            "jwt_secret": jwt_secret
        }
        
    # 如果环境变量不存在，从文件加载
    secret_path = Path(secret_dir)
    try:
        # 读取所有密钥
        with open(secret_path / "api_secret.key", "rb") as f:
            api_secret = f.read()
        
        with open(secret_path / "encryption.key", "rb") as f:
            encryption_key = f.read()
            
        with open(secret_path / "jwt_secret.key", "r") as f:
            jwt_secret = f.read()
        
        return {
            "api_secret": api_secret,
            "encryption_key": encryption_key,
            "jwt_secret": jwt_secret
        }
    except FileNotFoundError:
        # 如果密钥文件不存在，生成新的密钥
        print("密钥文件不存在，正在生成新的密钥...")
        return save_api_keys(secret_dir)


# 加载或生成所有密钥
API_KEYS = load_api_keys()
API_SECRET_KEY = API_KEYS["api_secret"]
ENCRYPTION_KEY = API_KEYS["encryption_key"]
JWT_SECRET_KEY = API_KEYS["jwt_secret"]

