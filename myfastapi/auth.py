# myfastapi/auth.py
# 用于处理 JWT 令牌和密码哈希的工具模块
from datetime import datetime, timedelta, timezone
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Header, HTTPException, status  # Add Header
import logging
import uuid  # 添加uuid支持

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))
from config import DATABASE_URL

# 导入Redis黑名单管理
try:
    from .redis_client import get_token_blacklist
    REDIS_AVAILABLE = True
    token_blacklist_manager = get_token_blacklist()
    logger = logging.getLogger(__name__)
    logger.info("Redis Token黑名单功能已启用")
except ImportError as e:
    REDIS_AVAILABLE = False
    token_blacklist_manager = None
    logger = logging.getLogger(__name__)
    logger.warning(f"Redis不可用，Token黑名单功能已禁用: {e}")

# 配置日志
logger = logging.getLogger(__name__)

# JWT 配置
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # 新增：refresh token 过期时间

# 从环境变量或配置文件加载 JWT 密钥
def get_jwt_secret_key() -> str:
    """获取 JWT 密钥，从 security 模块获取"""
    try:
        from security import JWT_SECRET_KEY
        return JWT_SECRET_KEY
    except ImportError:
        # 如果无法从 security 模块导入，尝试从环境变量获取
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            raise ValueError("JWT secret key is not configured. Please ensure the security module is available or set JWT_SECRET environment variable.")
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
        
        # 添加唯一标识符用于黑名单管理
        jti = str(uuid.uuid4())  # JWT ID
        
        to_encode.update({
            "exp": expire,
            "iat": now,  # 令牌创建时间
            "jti": jti   # JWT ID用于黑名单
        })
        
        encoded_jwt = jwt.encode(to_encode, jwt_secret, algorithm=ALGORITHM)
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise ValueError(f"Token creation failed: {str(e)}")

# 新增：创建 refresh token
def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT refresh 令牌"""
    try:
        jwt_secret = get_jwt_secret_key()
        to_encode = data.copy()
        
        now = datetime.now(timezone.utc)
        if expires_delta:
            expire = now + expires_delta
        else:
            expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # 添加唯一标识符用于黑名单管理
        jti = str(uuid.uuid4())  # JWT ID
        
        to_encode.update({
            "exp": expire,
            "iat": now,
            "jti": jti,  # JWT ID用于黑名单
            "type": "refresh"  # 标记为 refresh token
        })
        
        encoded_jwt = jwt.encode(to_encode, jwt_secret, algorithm=ALGORITHM)
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Failed to create refresh token: {str(e)}")
        raise ValueError(f"Refresh token creation failed: {str(e)}")

def verify_token(token: str) -> Dict[str, Any]:
    """验证 JWT 令牌"""
    try:
        jwt_secret = get_jwt_secret_key()
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        
        # 检查Token是否在黑名单中
        if REDIS_AVAILABLE and token_blacklist_manager:
            jti = payload.get("jti")
            if jti:
                if token_blacklist_manager.is_token_revoked(jti):
                    logger.warning(f"Token {jti} 已被撤销")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail={
                            "message": "Token has been revoked",
                            "error_code": "TOKEN_REVOKED",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        },
                        headers={"WWW-Authenticate": "Bearer"},
                    )
        
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

def verify_refresh_token(token: str) -> Dict[str, Any]:
    """验证 refresh token"""
    try:
        jwt_secret = get_jwt_secret_key()
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM])
        
        # 验证是否为 refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 验证令牌是否过期
        exp = payload.get("exp")
        if not exp or datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return payload
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Could not validate refresh token", "error": str(e)},
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

async def get_current_user_from_token(authorization: str = Header(None)) -> Dict[str, Any]:  # Added type hint for return
    print("!!! AUTH: get_current_user_from_token FUNCTION ENTERED (via print) !!!")
    logging.getLogger().info("!!! AUTH: get_current_user_from_token FUNCTION ENTERED (via root logger) !!!")
    logger.info("get_current_user_from_token called (via named logger myfastapi.auth)") # Clarified logger name
    logger.debug(f"Authorization header: {authorization}") # New log
    """验证 JWT 令牌并返回当前用户"""
    if not authorization:
        logger.warning("Authorization header missing") # New log
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查令牌格式
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        logger.warning(f"Invalid authentication scheme: {scheme}") # New log
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证方案无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证令牌
    try:
        payload = verify_token(token)
        logger.info("Token verified successfully") # New log
        return payload
    except HTTPException as e: # Catch HTTPException from verify_token
        logger.error(f"Token verification failed: {e.detail}") # New log
        raise e # Re-raise the exception

def revoke_token(token: str) -> bool:
    """撤销Token并加入黑名单"""
    if not REDIS_AVAILABLE or not token_blacklist_manager:
        logger.warning("Redis不可用，无法撤销Token")
        return False
    
    try:
        # 解析token获取jti和过期时间
        jwt_secret = get_jwt_secret_key()
        payload = jwt.decode(token, jwt_secret, algorithms=[ALGORITHM], options={"verify_exp": False})
        
        jti = payload.get("jti")
        exp = payload.get("exp")
        
        if not jti:
            logger.warning("Token缺少jti字段，无法撤销")
            return False
        
        if not exp:
            logger.warning("Token缺少exp字段，无法撤销")
            return False
        
        # 计算剩余过期时间
        exp_time = datetime.fromtimestamp(exp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        if exp_time <= now:
            logger.info("Token已过期，无需加入黑名单")
            return True
        
        remaining_seconds = int((exp_time - now).total_seconds())
        
        # 加入黑名单
        return token_blacklist_manager.revoke_token(jti, remaining_seconds)
        
    except JWTError as e:
        logger.error(f"撤销Token失败，Token解析错误: {e}")
        return False
    except Exception as e:
        logger.error(f"撤销Token失败: {e}")
        return False

def revoke_all_user_tokens(user_id: str) -> bool:
    """撤销用户的所有Token (注意：这需要额外的Token跟踪机制)"""
    # 这个功能需要额外的实现，因为我们需要跟踪每个用户的所有活跃Token
    # 暂时返回False表示未实现
    logger.warning("撤销用户所有Token功能尚未实现")
    return False
