# myfastapi/auth.py
# 用于处理 JWT 令牌和密码哈希的工具模块
from datetime import datetime, timedelta, timezone
import os
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logging
from config import DATABASE_URL

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
    """创建 JWT 访问令牌"""
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
    """验证 JWT 令牌"""
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Could not validate credentials", "error": str(e)},
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)
