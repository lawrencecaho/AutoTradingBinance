from datetime import datetime, timedelta, timezone
import os
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logging

# 配置日志
logger = logging.getLogger(__name__)

# JWT 配置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# 从环境变量或配置文件加载 JWT 密钥
def get_jwt_secret_key() -> str:
    """获取 JWT 密钥，优先从环境变量获取"""
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        from config import JWT_SECRET_KEY
        jwt_secret = JWT_SECRET_KEY
    
    if not jwt_secret:
        raise ValueError("JWT secret key is not configured")
    return jwt_secret

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌
    
    Args:
        data (dict): 要编码到令牌中的数据
        expires_delta (Optional[timedelta]): 可选的过期时间增量
        
    Returns:
        str: 编码后的 JWT 令牌
        
    Raises:
        ValueError: 如果JWT密钥未配置或令牌创建失败
    """
    try:
        jwt_secret = get_jwt_secret_key()
        to_encode = data.copy()
        
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": now  # 令牌创建时间
        })
        
        encoded_jwt = jwt.encode(to_encode, jwt_secret, algorithm=ALGORITHM)
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise ValueError(f"Token creation failed: {str(e)}")

def verify_token(token: str) -> Dict[str, Any]:
    """
    验证 JWT 令牌
    
    Args:
        token (str): 要验证的 JWT 令牌
        
    Returns:
        Dict[str, Any]: 解码后的令牌载荷
        
    Raises:
        HTTPException: 如果令牌无效或已过期
    """
    try:
        jwt_secret = get_jwt_secret_key()
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        
        # 验证令牌是否过期
        exp = payload.get("exp")
        if not exp or datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "message": "Token has expired",
                    "error_code": "TOKEN_EXPIRED",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "exp_time": datetime.fromtimestamp(exp, tz=timezone.utc).isoformat() if exp else None
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
        
    except JWTError as e:
        error_detail = {
            "message": "Invalid authentication credentials",
            "error_code": "INVALID_TOKEN",
            "error_type": e.__class__.__name__,
            "error_details": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.error(f"JWT verification failed: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        error_detail = {
            "message": "Token verification failed",
            "error_code": "TOKEN_VERIFICATION_ERROR",
            "error_type": e.__class__.__name__,
            "error_details": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.error(f"Token verification error: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否匹配哈希密码
    
    Args:
        plain_password (str): 明文密码
        hashed_password (str): 数据库中存储的哈希密码
        
    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    对密码进行哈希处理
    
    Args:
        password (str): 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)

def get_current_user(token: str) -> Dict[str, Any]:
    """
    从JWT令牌获取当前用户信息
    
    Args:
        token (str): JWT令牌
        
    Returns:
        Dict[str, Any]: 用户信息
        
    Raises:
        HTTPException: 如果令牌无效或用户不存在
    """
    payload = verify_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        error_detail = {
            "message": "Could not validate credentials",
            "error_code": "MISSING_USER_ID",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload_keys": list(payload.keys())
        }
        logger.error(f"User validation failed: {error_detail}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"user_id": user_id, **payload}
