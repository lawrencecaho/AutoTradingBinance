# fastapi/security.py
"""
用于处理 API 加密和签名的工具模块
"""
import os
import secrets
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from datetime import datetime
import hmac
import hashlib
import time
from typing import Dict, Any, Optional, Union, Tuple, cast
from fastapi import HTTPException, Header
import base64
import logging
from pathlib import Path

# 配置日志
logger = logging.getLogger(__name__)

# 定义密钥存储路径
KEY_DIRECTORY = Path(__file__).parent.parent / 'Secret'
PRIVATE_KEY_PATH = KEY_DIRECTORY / 'fastapi-private.pem'
PUBLIC_KEY_PATH = KEY_DIRECTORY / 'fastapi-public.pem'

def load_or_generate_rsa_keys() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """加载或生成RSA密钥对"""
    try:
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

        # 如果密钥不存在，生成新密钥对
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        # 确保目录存在
        KEY_DIRECTORY.mkdir(parents=True, exist_ok=True)

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

        return private_key, public_key
    except Exception as e:
        logger.error(f"密钥生成或加载失败: {str(e)}")
        raise

# 初始化 RSA 密钥对
PRIVATE_KEY, PUBLIC_KEY = load_or_generate_rsa_keys()

def get_api_secret() -> bytes:
    """获取 API 密钥"""
    secret = os.getenv("API_SECRET_KEY")
    if not secret:
        try:
            from config import API_SECRET_KEY
            secret = API_SECRET_KEY
        except (ImportError, AttributeError):
            raise ValueError("API secret key not configured")

    return secret.encode() if isinstance(secret, str) else secret

# 初始化API密钥
API_SECRET_KEY = get_api_secret()

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
    if not all([x_api_key, x_timestamp, x_signature]):
        raise HTTPException(status_code=401, detail="Missing security headers")

    # 验证时间戳
    try:
        # 确保 x_timestamp 不为 None 并转换为整数
        if x_timestamp is None:
            raise ValueError("Timestamp is required")
        
        timestamp = int(x_timestamp)
        current_time = int(time.time() * 1000)
        if abs(current_time - timestamp) > 60000:  # 60秒超时
            raise HTTPException(status_code=401, detail="Timestamp expired")
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