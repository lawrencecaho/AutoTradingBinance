"""
用于处理 API 加密和签名的工具模块
"""
import os
import secrets
from cryptography.fernet import Fernet
import hmac
import hashlib
import time
from typing import Dict, Any, Optional, Union
from fastapi import HTTPException, Header
import base64
import logging

# 配置日志
logger = logging.getLogger(__name__)

def generate_fernet_key() -> bytes:
    """生成一个新的 Fernet 密钥"""
    return Fernet.generate_key()

def create_valid_key(key_material: Union[str, bytes]) -> bytes:
    """从任意密钥材料创建有效的 Fernet 密钥"""
    if isinstance(key_material, str):
        key_material = key_material.encode()
    # 使用 SHA-256 创建固定长度的密钥材料
    hashed = hashlib.sha256(key_material).digest()
    # 转换为 URL 安全的 base64 编码
    return base64.urlsafe_b64encode(hashed)

def get_encryption_key() -> bytes:
    """获取加密密钥，优先从环境变量获取"""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        # 如果环境变量不存在，从配置文件获取
        try:
            from config import ENCRYPTION_KEY
            key = ENCRYPTION_KEY
        except (ImportError, AttributeError):
            logger.warning("No encryption key found, generating a new one")
            return generate_fernet_key()

    try:
        # 尝试直接使用密钥
        if isinstance(key, bytes):
            Fernet(key)
            return key
        # 如果是字符串，创建有效的密钥
        return create_valid_key(key)
    except Exception as e:
        logger.error(f"Invalid encryption key format: {str(e)}")
        logger.warning("Generating a new encryption key")
        return generate_fernet_key()

def get_api_secret() -> bytes:
    """获取 API 密钥，优先从环境变量获取"""
    secret = os.getenv("API_SECRET_KEY")
    if not secret:
        try:
            from config import API_SECRET_KEY
            secret = API_SECRET_KEY
        except (ImportError, AttributeError):
            raise ValueError("API secret key not configured")

    return secret.encode() if isinstance(secret, str) else secret

# 初始化加密密钥
ENCRYPTION_KEY = get_encryption_key()
API_SECRET_KEY = get_api_secret()

# 创建 Fernet 实例
try:
    fernet = Fernet(ENCRYPTION_KEY)
    logger.info("Successfully initialized Fernet encryption")
except Exception as e:
    logger.error(f"Failed to initialize Fernet: {str(e)}")
    raise ValueError(f"Failed to initialize Fernet with encryption key: {str(e)}")

def encrypt_data(data: str) -> str:
    """使用 Fernet 加密数据"""
    try:
        return fernet.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Encryption failed")

def decrypt_data(encrypted_data: str) -> str:
    """使用 Fernet 解密数据"""
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid encrypted data")

def generate_signature(data: str, timestamp: str) -> str:
    """
    生成请求签名
    签名格式：HMAC-SHA256(data + timestamp, API_SECRET_KEY)
    """
    try:
        message = f"{data}{timestamp}".encode()
        signature = hmac.new(API_SECRET_KEY, message, hashlib.sha256).hexdigest()
        return signature
    except Exception as e:
        logger.error(f"Signature generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate signature")

def verify_request_timestamp(timestamp: str, max_age: Optional[int] = None) -> None:
    """
    验证请求时间戳是否在允许的时间范围内
    从环境变量获取超时设置，默认 5 分钟（300 秒）
    """
    try:
        max_request_age = int(os.getenv("MAX_REQUEST_AGE_SECONDS", "300"))
        if max_age is not None:
            max_request_age = max_age
            
        current_time = int(time.time())
        request_time = int(int(timestamp) / 1000)  # 转换毫秒为秒
        
        if current_time - request_time > max_request_age:
            raise HTTPException(
                status_code=400,
                detail=f"Request expired. Maximum age is {max_request_age} seconds"
            )
    except ValueError as e:
        logger.error(f"Invalid timestamp format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid timestamp format: {str(e)}")

def verify_signature(data: str, timestamp: str, signature: str) -> None:
    """验证请求签名"""
    try:
        expected_signature = generate_signature(data, timestamp)
        if not hmac.compare_digest(signature.lower(), expected_signature.lower()):
            raise HTTPException(status_code=401, detail="Invalid signature")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signature verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify signature")

async def verify_security_headers(
    x_timestamp: str = Header(...),
    x_signature: str = Header(...),
    x_request_id: str = Header(...)
) -> Dict[str, str]:
    """验证请求头中的安全相关字段"""
    verify_request_timestamp(x_timestamp)
    return {
        "timestamp": x_timestamp,
        "signature": x_signature,
        "request_id": x_request_id
    }

def get_security_info() -> Dict[str, Any]:
    """获取需要与前端共享的安全信息"""
    return {
        "encryption_key": ENCRYPTION_KEY.decode(),
        "signature_format": "HMAC-SHA256(data + timestamp, API_SECRET_KEY)",
        "timestamp_format": "milliseconds since epoch",
        "max_age": int(os.getenv("MAX_REQUEST_AGE_SECONDS", "300")) * 1000  # 转换为毫秒
    }
