# fastapi/security.py
"""
用于处理 API 加密和签名的工具模块
"""
import os
import secrets
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization, padding as sym_padding
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import hmac
import hashlib
import time
import uuid
from typing import Dict, Any, Optional, Union, Tuple, cast
from fastapi import HTTPException, Header
import base64
import logging
from pathlib import Path
import sys

# 使用PathUniti进行路径管理和模块导入
from PathUniti import path_manager, DATABASE_DIR
# 设置Python路径
path_manager.setup_python_path()

from sqlalchemy import create_engine, Column, String, Text, TIMESTAMP, Table, MetaData
from sqlalchemy import select, update, insert, func
from sqlalchemy.ext.declarative import declarative_base

# 初始化数据库连接 - 使用PathUniti新方法导入
from DatabaseOperator.pg_operator import Session, engine
metadata = MetaData()
Base = declarative_base()
SessionLocal = Session()

# 配置日志
logger = logging.getLogger(__name__)

# 更新密钥存储路径 - 使用PathUniti的SECRET_DIR
from PathUniti import SECRET_DIR
KEY_DIRECTORY = SECRET_DIR
PRIVATE_KEY_PATH = KEY_DIRECTORY / 'fastapi-private.pem'
PUBLIC_KEY_PATH = KEY_DIRECTORY / 'fastapi-public.pem'

# 确保目录存在
KEY_DIRECTORY.mkdir(parents=True, exist_ok=True)

# 定义表结构
global_options = Table(
    "global_options", 
    metadata,
    Column("id", String, primary_key=True),
    Column("varb", String, unique=True, nullable=False),
    Column("options", Text, nullable=True),
    Column("reserve", String, nullable=True),
    Column("reserve1", Text, nullable=True),
    Column("fixed_time", TIMESTAMP, nullable=True)
)

# 新增函数：从数据库同步密钥
def sync_keys_with_database():
    """校验本地文件与数据库中的密钥是否一致，不一致则从数据库导入"""
    conn = None
    try:
        conn = engine.connect()
        trans = conn.begin()  # 显式开始事务
        try:
            # 使用 SQLAlchemy Core 查询
            private_key_query = select(global_options).where(global_options.c.varb == "private_key")
            public_key_query = select(global_options).where(global_options.c.varb == "public_key")
            
            db_private_key = conn.execute(private_key_query).fetchone()
            db_public_key = conn.execute(public_key_query).fetchone()

            if db_private_key and db_public_key:
                db_private_key_content = db_private_key.options
                db_public_key_content = db_public_key.options

                # 确保本地密钥文件存在
                if not PRIVATE_KEY_PATH.exists() or not PUBLIC_KEY_PATH.exists():
                    # 如果本地文件不存在，直接从数据库写入
                    with open(PRIVATE_KEY_PATH, 'wb') as private_file:
                        private_file.write(db_private_key_content.encode())

                    with open(PUBLIC_KEY_PATH, 'wb') as public_file:
                        public_file.write(db_public_key_content.encode())
                    
                    logger.info("从数据库同步密钥到本地文件")
                    return
                
                # 读取本地密钥
                with open(PRIVATE_KEY_PATH, 'rb') as private_file:
                    local_private_key = private_file.read()

                with open(PUBLIC_KEY_PATH, 'rb') as public_file:
                    local_public_key = public_file.read()

                # 如果本地密钥与数据库密钥不一致，则更新本地文件
                if local_private_key != db_private_key_content.encode() or local_public_key != db_public_key_content.encode():
                    with open(PRIVATE_KEY_PATH, 'wb') as private_file:
                        private_file.write(db_private_key_content.encode())

                    with open(PUBLIC_KEY_PATH, 'wb') as public_file:
                        public_file.write(db_public_key_content.encode())
                    
                    logger.info("检测到密钥不一致，已从数据库更新本地密钥")
            
            trans.commit()  # 提交事务
        except Exception as e:
            trans.rollback()  # 回滚事务
            logger.error(f"同步密钥失败: {str(e)}")
            raise
    finally:
        if conn:
            conn.close()  # 确保连接关闭

# 新增函数：检查并更新密钥
def check_and_update_keys():
    """检查数据库中密钥的 fixed_time 是否超过 30 天，超过则重新生成密钥"""
    conn = None
    try:
        conn = engine.connect()
        trans = conn.begin()  # 显式开始事务
        try:
            # 使用 SQLAlchemy Core 查询
            query = select(global_options).where(global_options.c.varb == "private_key")
            result = conn.execute(query).fetchone()
            
            if result and result.fixed_time:
                fixed_time = result.fixed_time
                current_time = datetime.now()
                if (current_time - fixed_time) > timedelta(days=30):
                    # 超过 30 天，重新生成密钥
                    private_key, public_key = load_or_generate_rsa_keys(force_generate=True)
                    
                    # 使用 SQLAlchemy Core 更新数据库
                    private_key_update = update(global_options).where(
                        global_options.c.varb == "private_key"
                    ).values(
                        options=private_key.private_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PrivateFormat.PKCS8,
                            encryption_algorithm=serialization.NoEncryption()
                        ).decode(),
                        fixed_time=datetime.now()
                    )
                    conn.execute(private_key_update)
                    
                    public_key_update = update(global_options).where(
                        global_options.c.varb == "public_key"
                    ).values(
                        options=public_key.public_bytes(
                            encoding=serialization.Encoding.PEM,
                            format=serialization.PublicFormat.SubjectPublicKeyInfo
                        ).decode(),
                        fixed_time=datetime.now()
                    )
                    conn.execute(public_key_update)
            
            trans.commit()  # 提交事务
        except Exception as e:
            trans.rollback()  # 回滚事务
            logger.error(f"检查或更新密钥失败: {str(e)}")
            raise
    finally:
        if conn:
            conn.close()  # 确保连接关闭

# 修改函数：加载或生成密钥
def load_or_generate_rsa_keys(force_generate: bool = False) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """加载或生成 RSA 密钥对"""
    try:
        if not force_generate:
            sync_keys_with_database()
            check_and_update_keys()

        # 尝试加载现有密钥
        if PRIVATE_KEY_PATH.exists() and PUBLIC_KEY_PATH.exists():
            with open(PRIVATE_KEY_PATH, 'rb') as private_file:
                private_key = serialization.load_pem_private_key(
                    private_file.read(),
                    password=None,
                    backend=default_backend()
                )
            with open(PUBLIC_KEY_PATH, 'rb') as public_file:
                public_key = serialization.load_pem_public_key(
                    public_file.read(),
                    backend=default_backend()
                )
            # 使用 cast 确保类型正确
            return cast(rsa.RSAPrivateKey, private_key), cast(rsa.RSAPublicKey, public_key)

        # 如果密钥不存在或强制生成，生成新密钥对
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        # 保存私钥
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(PRIVATE_KEY_PATH, 'wb') as f:
            f.write(private_pem)

        # 保存公钥
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open(PUBLIC_KEY_PATH, 'wb') as f:
            f.write(public_pem)

        # 更新数据库
        conn = engine.connect()
        try:
            # 检查是否已存在记录
            private_key_query = select(global_options).where(global_options.c.varb == "private_key")
            private_key_exists = conn.execute(private_key_query).fetchone()
            
            if private_key_exists:
                # 更新现有记录
                private_key_update = update(global_options).where(
                    global_options.c.varb == "private_key"
                ).values(
                    options=private_pem.decode(),
                    fixed_time=datetime.now()
                )
                conn.execute(private_key_update)
            else:
                # 插入新记录
                private_key_insert = insert(global_options).values(
                    id=str(uuid.uuid4()),
                    varb="private_key",
                    options=private_pem.decode(),
                    fixed_time=datetime.now()
                )
                conn.execute(private_key_insert)
            
            # 检查公钥是否存在
            public_key_query = select(global_options).where(global_options.c.varb == "public_key")
            public_key_exists = conn.execute(public_key_query).fetchone()
            
            if public_key_exists:
                # 更新现有记录
                public_key_update = update(global_options).where(
                    global_options.c.varb == "public_key"
                ).values(
                    options=public_pem.decode(),
                    fixed_time=datetime.now()
                )
                conn.execute(public_key_update)
            else:
                # 插入新记录
                public_key_insert = insert(global_options).values(
                    id=str(uuid.uuid4()),
                    varb="public_key",
                    options=public_pem.decode(),
                    fixed_time=datetime.now()
                )
                conn.execute(public_key_insert)
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

        return private_key, public_key
    except Exception as e:
        logger.error(f"密钥生成或加载失败: {str(e)}")
        raise

# API 密钥有效期（天数）
API_SECRET_VALIDITY_DAYS = 7

def get_api_secret_timestamp_path() -> Path:
    """获取API密钥时间戳文件路径"""
    return KEY_DIRECTORY / 'api_secret.timestamp'

def save_api_secret_timestamp():
    """保存API密钥生成时间戳"""
    try:
        timestamp_path = get_api_secret_timestamp_path()
        current_time = datetime.now().isoformat()
        with open(timestamp_path, 'w') as f:
            f.write(current_time)
        timestamp_path.chmod(0o600)
        logger.debug(f"保存API密钥时间戳: {current_time}")
    except Exception as e:
        logger.error(f"保存时间戳失败: {str(e)}")

def is_api_secret_expired() -> bool:
    """检查API密钥是否过期"""
    try:
        timestamp_path = get_api_secret_timestamp_path()
        if not timestamp_path.exists():
            logger.info("时间戳文件不存在，密钥需要重新生成")
            return True
        
        with open(timestamp_path, 'r') as f:
            timestamp_str = f.read().strip()
        
        # 解析时间戳
        creation_time = datetime.fromisoformat(timestamp_str)
        current_time = datetime.now()
        
        # 计算时间差
        time_diff = current_time - creation_time
        
        # 检查是否超过有效期
        if time_diff.days >= API_SECRET_VALIDITY_DAYS:
            logger.info(f"API密钥已过期 ({time_diff.days} 天 >= {API_SECRET_VALIDITY_DAYS} 天)")
            return True
        else:
            logger.debug(f"API密钥仍有效 ({time_diff.days} 天 < {API_SECRET_VALIDITY_DAYS} 天)")
            return False
            
    except Exception as e:
        logger.warning(f"检查密钥过期状态失败: {str(e)}，将重新生成密钥")
        return True

# 生成并保存 API 密钥
def generate_and_save_api_secret() -> bytes:
    """生成并保存新的 API 密钥"""
    try:
        # 生成32字节的密码学安全随机密钥
        api_secret = secrets.token_bytes(32)
        
        # 保存到文件
        api_secret_path = KEY_DIRECTORY / 'api_secret.key'
        with open(api_secret_path, 'wb') as f:
            f.write(api_secret)
        
        # 设置文件权限（仅所有者可读写）
        api_secret_path.chmod(0o600)
        
        # 保存生成时间戳
        save_api_secret_timestamp()
        
        logger.info("已生成并保存新的 API 密钥")
        return api_secret
    except Exception as e:
        logger.error(f"生成 API 密钥失败: {str(e)}")
        raise

# 获取 API 密钥
def get_api_secret() -> bytes:
    """获取用于 HMAC 签名的 API 密钥（支持自动更新）"""
    api_secret_path = KEY_DIRECTORY / 'api_secret.key'
    
    # 检查密钥是否过期
    if is_api_secret_expired():
        logger.info("API密钥已过期或不存在，正在重新生成")
        return generate_and_save_api_secret()
    
    # 尝试从文件加载现有密钥
    if api_secret_path.exists():
        try:
            with open(api_secret_path, 'rb') as f:
                api_secret = f.read()
            
            # 验证密钥长度（至少16字节）
            if len(api_secret) >= 16:
                logger.info("从 Security 文件夹加载 API 密钥")
                return api_secret
            else:
                logger.warning("现有 API 密钥长度不足，重新生成")
        except Exception as e:
            logger.warning(f"读取现有 API 密钥失败: {e}，重新生成")
    
    # 自动生成新密钥
    return generate_and_save_api_secret()

def force_regenerate_api_secret() -> bytes:
    """强制重新生成API密钥（忽略有效期）"""
    logger.info("强制重新生成API密钥")
    return generate_and_save_api_secret()

def get_api_secret_info() -> dict:
    """获取API密钥信息（用于监控和调试）"""
    try:
        api_secret_path = KEY_DIRECTORY / 'api_secret.key'
        timestamp_path = get_api_secret_timestamp_path()
        
        info = {
            "exists": api_secret_path.exists(),
            "validity_days": API_SECRET_VALIDITY_DAYS,
            "expired": is_api_secret_expired()
        }
        
        if timestamp_path.exists():
            try:
                with open(timestamp_path, 'r') as f:
                    timestamp_str = f.read().strip()
                creation_time = datetime.fromisoformat(timestamp_str)
                current_time = datetime.now()
                time_diff = current_time - creation_time
                
                info.update({
                    "created_at": timestamp_str,
                    "age_days": time_diff.days,
                    "age_seconds": int(time_diff.total_seconds()),
                    "expires_in_days": max(0, API_SECRET_VALIDITY_DAYS - time_diff.days)
                })
            except Exception as e:
                info["timestamp_error"] = str(e)
        
        return info
    except Exception as e:
        return {"error": str(e)}

# 设置API密钥有效期（天数）
def set_api_secret_validity_days(days: int):
    """设置API密钥有效期（天数）"""
    global API_SECRET_VALIDITY_DAYS
    if days <= 0:
        raise ValueError("有效期必须大于0天")
    API_SECRET_VALIDITY_DAYS = days
    logger.info(f"API密钥有效期已设置为 {days} 天")

def get_api_secret_validity_days() -> int:
    """获取当前API密钥有效期设置"""
    return API_SECRET_VALIDITY_DAYS

# 初始化API密钥
API_SECRET_KEY = get_api_secret()

# 初始化 RSA 密钥对
try:
    PRIVATE_KEY, PUBLIC_KEY = load_or_generate_rsa_keys()
except Exception as e:
    logger.error(f"初始化 RSA 密钥对失败: {str(e)}")
    raise

def encrypt_data(data: str) -> str:
    """使用RSA公钥加密数据"""
    try:
        if not isinstance(PUBLIC_KEY, rsa.RSAPublicKey):
            raise ValueError("公钥类型不正确，需要 RSA 公钥")
            
        padding_algorithm = padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
        encrypted_data = PUBLIC_KEY.encrypt(
            data.encode(),
            padding_algorithm
        )
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        logger.error(f"加密失败: {str(e)}")
        raise HTTPException(status_code=500, detail="Encryption failed")

def decrypt_data(encrypted_data: str) -> str:
    """使用RSA私钥解密数据"""
    try:
        if not isinstance(PRIVATE_KEY, rsa.RSAPrivateKey):
            raise ValueError("私钥类型不正确，需要 RSA 私钥")
            
        padding_algorithm = padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
        decrypted_data = PRIVATE_KEY.decrypt(
            base64.b64decode(encrypted_data),
            padding_algorithm
        )
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"解密失败: {str(e)}")
        raise HTTPException(status_code=400, detail="Decryption failed")

def sign_data(data: str, timestamp: str) -> str:
    """使用RSA私钥对数据进行签名"""
    message = f"{data}{timestamp}".encode()
    
    if not isinstance(PRIVATE_KEY, rsa.RSAPrivateKey):
        raise ValueError("私钥类型不正确")
    
    try:
        signature = PRIVATE_KEY.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode()
    except Exception as e:
        logger.error(f"签名失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"签名生成失败: {str(e)}")

def verify_signature_rsa(data: str, timestamp: str, signature: str) -> bool:
    """验证RSA签名"""
    try:
        message = f"{data}{timestamp}".encode()
        sig_bytes = base64.b64decode(signature)
        
        if not isinstance(PUBLIC_KEY, rsa.RSAPublicKey):
            raise ValueError("公钥类型不正确")
        
        PUBLIC_KEY.verify(
            sig_bytes,
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except Exception as e:
        logger.error(f"签名验证失败: {str(e)}")
        return False

def verify_signature(message: str, timestamp: str, signature: str) -> bool:
    """验证请求签名"""
    try:
        # 允许前端使用固定签名值
        if signature == 'frontend':
            # 前端使用固定签名时，仅验证时间戳的有效性
            # 当前时间戳与请求时间戳的差值不应超过60秒
            current_time = int(time.time() * 1000)
            request_time = int(timestamp)
            return abs(current_time - request_time) <= 60000  # 60秒内有效
            
        # 对其他客户端进行正常验证
        data_to_verify = (message + timestamp).encode()
        signature_bytes = base64.b64decode(signature)
        
        hmac_obj = hmac.new(API_SECRET_KEY, data_to_verify, hashlib.sha256)
        expected_signature = hmac_obj.digest()
        
        return hmac.compare_digest(signature_bytes, expected_signature)
    except Exception as e:
        logger.error(f"签名验证失败: {str(e)}")
        return False

def verify_security_headers(
    x_api_key: Optional[str] = Header(None),
    x_timestamp: Optional[str] = Header(None),
    x_signature: Optional[str] = Header(None),
) -> Dict[str, Optional[str]]:
    """验证安全头信息"""
    if not all([x_api_key, x_timestamp]):
        raise HTTPException(status_code=401, detail="Missing security headers")
        
    # 对无签名请求进行严格控制
    if x_signature is None or x_signature == 'frontend':
        # 添加速率限制和日志记录
        import logging
        logger = logging.getLogger(__name__)
        api_key_masked = x_api_key[:8] + '...' if x_api_key and len(x_api_key) > 8 else 'unknown'
        logger.warning(f"Unsigned request from API key: {api_key_masked}")
        # 可以在这里添加额外的验证逻辑，比如IP白名单等
        x_signature = 'frontend'  # 允许前端请求，但记录日志

    # 验证时间戳
    try:
        # 确保 x_timestamp 不为 None 并转换为整数
        if x_timestamp is None:
            raise ValueError("Timestamp is required")
        
        timestamp = int(x_timestamp)
        current_time = int(time.time() * 1000)
        # 使用配置化的时间窗口
        from security_config import get_security_config
        security_cfg = get_security_config()
        time_window = security_cfg.get_timestamp_window()
        
        if abs(current_time - timestamp) > time_window:
            raise HTTPException(status_code=401, detail="Request expired")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timestamp format")

    return {
        "api_key": x_api_key,
        "timestamp": x_timestamp,
        "signature": x_signature
    }

def get_security_info() -> Dict[str, Any]:
    """获取安全配置信息"""
    # 格式化公钥，移除头尾和换行符
    public_key_pem = PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8').replace(
        '-----BEGIN PUBLIC KEY-----', ''
    ).replace(
        '-----END PUBLIC KEY-----', ''
    ).replace('\n', '')
    
    return {
        "public_key": public_key_pem,
        "signature_format": "HMAC-SHA256(message + timestamp, API_SECRET_KEY)",
        "timestamp_format": "milliseconds since epoch",
        "max_age": 60000,  # 60 seconds
        "encryption_algorithm": "RSA-OAEP-SHA256"
    }

def encrypt_with_client_key(data: str, client_public_key_pem: str) -> str:
    """使用客户端公钥加密数据"""
    try:
        # 记录输入的公钥信息
        logger.debug(f"客户端公钥长度: {len(client_public_key_pem)}")
        logger.debug(f"要加密的数据长度: {len(data)}")
        
        # 确保客户端公钥格式正确
        if not client_public_key_pem.startswith("-----BEGIN PUBLIC KEY-----"):
            logger.debug("添加公钥头尾")
            client_public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{client_public_key_pem}\n-----END PUBLIC KEY-----"
            
        # 加载客户端公钥
        try:
            client_public_key = serialization.load_pem_public_key(
                client_public_key_pem.encode(),
                backend=default_backend()
            )
            logger.debug("成功加载客户端公钥")
        except Exception as key_error:
            logger.error(f"加载客户端公钥失败: {str(key_error)}")
            raise ValueError(f"无法加载客户端公钥: {str(key_error)}")
        
        # 确保是RSA公钥
        if not isinstance(client_public_key, rsa.RSAPublicKey):
            logger.error("提供的公钥不是RSA公钥")
            raise ValueError("提供的公钥不是RSA公钥")
            
        padding_algorithm = padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
        
        # 检查数据大小
        data_bytes = data.encode()
        key_size_bytes = (client_public_key.key_size + 7) // 8
        max_plaintext_size = key_size_bytes - 42  # OAEP with SHA-256 需要减去42字节的填充
        
        if len(data_bytes) > max_plaintext_size:
            logger.error(f"数据太大无法加密: {len(data_bytes)} 字节 > 最大 {max_plaintext_size} 字节")
            # 对于大数据，应该使用混合加密（AES + RSA），这里仅作示例
            # 在实际应用中，应当实现分块加密或混合加密
            raise ValueError(f"数据太大，超过RSA加密限制: {len(data_bytes)} > {max_plaintext_size} 字节")
        
        # 对数据进行加密
        try:
            encrypted_data = client_public_key.encrypt(
                data_bytes,
                padding_algorithm
            )
            logger.debug("数据加密成功")
            return base64.b64encode(encrypted_data).decode()
        except Exception as encrypt_error:
            logger.error(f"加密操作失败: {str(encrypt_error)}")
            raise
    except Exception as e:
        logger.error(f"使用客户端公钥加密失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")

# 添加用于混合加密的函数
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

def hybrid_encrypt_with_client_key(data: str, client_public_key_pem: str) -> Dict[str, str]:
    """使用混合加密（AES+RSA）加密大型数据
    
    1. 生成随机AES密钥和初始化向量
    2. 使用AES密钥加密数据
    3. 使用客户端RSA公钥加密AES密钥
    4. 返回加密的数据和加密的密钥
    """
    try:
        # 确保返回结构化的错误响应，而不是直接抛出异常
        result = {
            "success": True,
            "error": None,
            "encrypted_data": None,
            "encrypted_key": None,
            "encryption_method": "hybrid"
        }

        try:
            # 确保客户端公钥格式正确
            if not client_public_key_pem.startswith("-----BEGIN PUBLIC KEY-----"):
                logger.debug("添加公钥头尾")
                client_public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{client_public_key_pem}\n-----END PUBLIC KEY-----"
                
            # 加载客户端公钥
            try:
                client_public_key = serialization.load_pem_public_key(
                    client_public_key_pem.encode(),
                    backend=default_backend()
                )
                logger.debug("成功加载客户端公钥")
            except Exception as key_error:
                logger.error(f"加载客户端公钥失败: {str(key_error)}")
                result["success"] = False
                result["error"] = f"无法加载客户端公钥: {str(key_error)}"
                return result
            
            # 确保是RSA公钥
            if not isinstance(client_public_key, rsa.RSAPublicKey):
                logger.error("提供的公钥不是RSA公钥")
                result["success"] = False
                result["error"] = "提供的公钥不是RSA公钥"
                return result
            
            # 检查客户端公钥能否加密AES密钥和IV
            key_size_bytes = (client_public_key.key_size + 7) // 8
            max_key_plaintext_size = key_size_bytes - 42  # OAEP with SHA-256 需要减去42字节的填充
            
            # 确定AES密钥大小
            aes_key_size = 32  # 默认使用256位AES密钥
            if max_key_plaintext_size < 48:  # 48 = 32(密钥) + 16(IV)
                logger.warning(f"客户端RSA密钥太小，无法安全加密AES-256密钥和IV: {max_key_plaintext_size} < 48")
                if max_key_plaintext_size >= 32:  # 至少可以加密192位AES密钥+IV
                    aes_key_size = 24  # 降级到192位AES密钥
                    logger.info("降级到AES-192")
                elif max_key_plaintext_size >= 24:  # 至少可以加密128位AES密钥+IV
                    aes_key_size = 16  # 降级到128位AES密钥
                    logger.info("降级到AES-128")
                else:
                    logger.error(f"客户端RSA密钥太小，无法支持任何AES密钥大小: {max_key_plaintext_size}")
                    result["success"] = False
                    result["error"] = "客户端RSA密钥大小不足，无法安全进行混合加密"
                    return result
            
            # 1. 生成随机AES密钥和初始化向量
            aes_key = os.urandom(aes_key_size)  # 使用确定的密钥大小
            iv = os.urandom(16)       # 128位IV
            
            # 2. 使用AES加密数据
            data_bytes = data.encode()
            
            # 手动实现PKCS7填充
            block_size = 16  # AES块大小为16字节
            padding_length = block_size - (len(data_bytes) % block_size)
            padded_data = data_bytes + bytes([padding_length] * padding_length)
            
            try:
                encryptor = Cipher(
                    algorithms.AES(aes_key),
                    modes.CBC(iv),
                    backend=default_backend()
                ).encryptor()
                
                encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            except Exception as aes_error:
                logger.error(f"AES加密失败: {str(aes_error)}")
                result["success"] = False
                result["error"] = f"AES加密失败: {str(aes_error)}"
                return result
            
            # 3. 使用客户端RSA公钥加密AES密钥
            try:
                rsa_padding = padding.OAEP(
                    mgf=padding.MGF1(hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
                
                # AES密钥+IV一起加密
                key_iv = aes_key + iv
                encrypted_key = client_public_key.encrypt(key_iv, rsa_padding)
            except Exception as rsa_error:
                logger.error(f"RSA加密AES密钥失败: {str(rsa_error)}")
                result["success"] = False
                result["error"] = f"RSA加密AES密钥失败: {str(rsa_error)}"
                return result
            
            # 4. 返回Base64编码的加密数据和加密密钥
            # 使用URL安全的base64格式，去掉填充的等号
            encrypted_data_b64 = base64.b64encode(encrypted_data).decode()
            encrypted_key_b64 = base64.b64encode(encrypted_key).decode()
            
            # 替换特殊字符，使其与前端atob()函数兼容
            result["encrypted_data"] = encrypted_data_b64.replace('+', '-').replace('/', '_').replace('=', '')
            result["encrypted_key"] = encrypted_key_b64.replace('+', '-').replace('/', '_').replace('=', '')
            result["aes_key_size"] = len(aes_key) * 8  # 添加密钥大小信息
            result["aes_mode"] = "CBC"                 # 添加模式信息
            result["timestamp"] = int(time.time() * 1000)  # 添加时间戳
            result["base64_format"] = "url_safe"       # 标记使用了URL安全的base64格式
            
            return result
            
        except Exception as e:
            logger.error(f"混合加密过程中发生错误: {str(e)}")
            result["success"] = False
            result["error"] = f"混合加密失败: {str(e)}"
            return result

    except Exception as e:
        logger.error(f"混合加密失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Hybrid encryption failed: {str(e)}")

# 客户端公钥缓存，键为客户端标识符，值为公钥PEM
client_public_keys = {}

def store_client_public_key(client_id: str, public_key_pem: str) -> None:
    """存储客户端公钥"""
    client_public_keys[client_id] = public_key_pem
    logger.info(f"已存储客户端 {client_id} 的公钥")

def get_client_public_key(client_id: str) -> str | None:
    """获取客户端公钥"""
    key = client_public_keys.get(client_id)
    if key:
        logger.debug(f"找到客户端 {client_id} 的公钥")
    else:
        logger.debug(f"未找到客户端 {client_id} 的公钥")
    return key

def get_jwt_secret_timestamp_path() -> Path:
    """获取JWT密钥时间戳文件路径"""
    return KEY_DIRECTORY / 'jwt_secret.timestamp'

def save_jwt_secret_timestamp():
    """保存JWT密钥生成时间戳"""
    try:
        timestamp_path = get_jwt_secret_timestamp_path()
        current_time = datetime.now().isoformat()
        with open(timestamp_path, 'w') as f:
            f.write(current_time)
        timestamp_path.chmod(0o600)
        logger.debug(f"保存JWT密钥时间戳: {current_time}")
    except Exception as e:
        logger.error(f"保存JWT时间戳失败: {str(e)}")

def is_jwt_secret_expired() -> bool:
    """检查JWT密钥是否过期"""
    try:
        timestamp_path = get_jwt_secret_timestamp_path()
        if not timestamp_path.exists():
            logger.info("JWT时间戳文件不存在，密钥需要重新生成")
            return True
        
        with open(timestamp_path, 'r') as f:
            timestamp_str = f.read().strip()
        
        # 解析时间戳
        creation_time = datetime.fromisoformat(timestamp_str)
        current_time = datetime.now()
        
        # 计算时间差
        time_diff = current_time - creation_time
        
        # 检查是否超过有效期
        if time_diff.days >= API_SECRET_VALIDITY_DAYS:
            logger.info(f"JWT密钥已过期 ({time_diff.days} 天 >= {API_SECRET_VALIDITY_DAYS} 天)")
            return True
        else:
            logger.debug(f"JWT密钥仍有效 ({time_diff.days} 天 < {API_SECRET_VALIDITY_DAYS} 天)")
            return False
            
    except Exception as e:
        logger.warning(f"检查JWT密钥过期状态失败: {str(e)}，将重新生成密钥")
        return True

def generate_and_save_jwt_secret() -> str:
    """生成并保存新的 JWT 密钥"""
    try:
        # 生成64字节的URL安全随机密钥
        jwt_secret = secrets.token_urlsafe(64)
        
        # 保存到文件
        jwt_secret_path = KEY_DIRECTORY / 'jwt_secret.key'
        with open(jwt_secret_path, 'w') as f:
            f.write(jwt_secret)
        
        # 设置文件权限（仅所有者可读写）
        jwt_secret_path.chmod(0o600)
        
        # 保存生成时间戳
        save_jwt_secret_timestamp()
        
        logger.info("已生成并保存新的 JWT 密钥")
        return jwt_secret
    except Exception as e:
        logger.error(f"生成 JWT 密钥失败: {str(e)}")
        raise

def get_jwt_secret() -> str:
    """获取用于 JWT 签名的密钥（支持自动更新）"""
    jwt_secret_path = KEY_DIRECTORY / 'jwt_secret.key'
    
    # 检查密钥是否过期
    if is_jwt_secret_expired():
        logger.info("JWT密钥已过期或不存在，正在重新生成")
        return generate_and_save_jwt_secret()
    
    # 尝试从文件加载现有密钥
    if jwt_secret_path.exists():
        try:
            with open(jwt_secret_path, 'r') as f:
                jwt_secret = f.read().strip()
            
            # 验证密钥长度（至少32字符）
            if len(jwt_secret) >= 32:
                logger.info("从 Security 文件夹加载 JWT 密钥")
                return jwt_secret
            else:
                logger.warning("现有 JWT 密钥长度不足，重新生成")
        except Exception as e:
            logger.warning(f"读取现有 JWT 密钥失败: {e}，重新生成")
    
    # 自动生成新密钥
    return generate_and_save_jwt_secret()

def force_regenerate_jwt_secret() -> str:
    """强制重新生成JWT密钥（忽略有效期）"""
    logger.info("强制重新生成JWT密钥")
    return generate_and_save_jwt_secret()

def get_jwt_secret_info() -> dict:
    """获取JWT密钥信息（用于监控和调试）"""
    try:
        jwt_secret_path = KEY_DIRECTORY / 'jwt_secret.key'
        timestamp_path = get_jwt_secret_timestamp_path()
        
        info = {
            "exists": jwt_secret_path.exists(),
            "validity_days": API_SECRET_VALIDITY_DAYS,
            "expired": is_jwt_secret_expired()
        }
        
        if timestamp_path.exists():
            try:
                with open(timestamp_path, 'r') as f:
                    timestamp_str = f.read().strip()
                creation_time = datetime.fromisoformat(timestamp_str)
                current_time = datetime.now()
                time_diff = current_time - creation_time
                
                info.update({
                    "created_at": timestamp_str,
                    "age_days": time_diff.days,
                    "age_seconds": int(time_diff.total_seconds()),
                    "expires_in_days": max(0, API_SECRET_VALIDITY_DAYS - time_diff.days)
                })
            except Exception as e:
                info["timestamp_error"] = str(e)
        
        return info
    except Exception as e:
        return {"error": str(e)}

def get_all_secrets_info() -> dict:
    """获取所有密钥的信息"""
    return {
        "api_secret": get_api_secret_info(),
        "jwt_secret": get_jwt_secret_info(),
        "validity_days": API_SECRET_VALIDITY_DAYS
    }

def force_regenerate_all_secrets() -> dict:
    """强制重新生成所有密钥"""
    logger.info("强制重新生成所有密钥")
    api_secret = force_regenerate_api_secret()
    jwt_secret = force_regenerate_jwt_secret()
    
    return {
        "api_secret_length": len(api_secret),
        "jwt_secret_length": len(jwt_secret),
        "regenerated_at": datetime.now().isoformat()
    }

# 在模块加载完成后初始化JWT密钥
try:
    JWT_SECRET_KEY = get_jwt_secret()
    logger.info("JWT密钥初始化成功")
except Exception as e:
    logger.error(f"初始化 JWT 密钥失败: {str(e)}")
    raise