# myfastapi/redis_client.py
"""
Redis客户端配置和管理模块
用于Token黑名单、会话管理和缓存
"""
import os
import redis
import logging
import json
from typing import Optional, Union, Any, Dict, List
from datetime import datetime, timedelta

# 配置日志
logger = logging.getLogger(__name__)

class RedisClient:
    """Redis客户端单例类"""
    _instance = None
    _redis_client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._redis_client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """初始化Redis客户端"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            redis_password = os.getenv("REDIS_PASSWORD", "")
            redis_db = int(os.getenv("REDIS_DB", 0))
            
            # 解析Redis URL并添加密码
            if redis_password and "://" in redis_url:
                # 如果有密码但URL中没有密码，添加密码
                if "@" not in redis_url.split("://")[1]:
                    protocol, rest = redis_url.split("://", 1)
                    redis_url = f"{protocol}://:{redis_password}@{rest}"
            
            # 创建连接池
            self._redis_client = redis.Redis.from_url(
                redis_url,
                password=redis_password if redis_password else None,
                db=redis_db,
                decode_responses=True,  # 自动解码为字符串
                max_connections=20,     # 连接池大小
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                health_check_interval=30
            )
            
            # 测试连接
            self._redis_client.ping()
            logger.info("Redis客户端初始化成功")
            
        except Exception as e:
            logger.error(f"Redis客户端初始化失败: {e}")
            self._redis_client = None
            raise
    
    @property
    def client(self) -> redis.Redis:
        """获取Redis客户端实例"""
        if self._redis_client is None:
            self._initialize_client()
        if self._redis_client is None:
            raise RuntimeError("Redis客户端初始化失败")
        return self._redis_client
    
    def is_connected(self) -> bool:
        """检查Redis连接状态"""
        try:
            if self._redis_client is None:
                return False
            response = self._redis_client.ping()
            return bool(response)
        except Exception as e:
            logger.warning(f"Redis连接检查失败: {e}")
            return False
    
    def get_info(self) -> Dict[str, Any]:
        """获取Redis服务器信息"""
        try:
            if self._redis_client is None:
                return {}
            info = self._redis_client.info()
            return info if isinstance(info, dict) else {}
        except Exception as e:
            logger.error(f"获取Redis信息失败: {e}")
            return {}

class TokenBlacklist:
    """Token黑名单管理"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client.client
        self.prefix = "blacklist:"
    
    def revoke_token(self, jti: str, expires_in: int) -> bool:
        """
        将token加入黑名单
        
        Args:
            jti: JWT ID
            expires_in: 过期时间（秒）
        
        Returns:
            bool: 是否成功添加到黑名单
        """
        try:
            key = f"{self.prefix}{jti}"
            revoke_data = {
                "revoked_at": datetime.utcnow().isoformat(),
                "expires_in": expires_in
            }
            
            # 设置过期时间，避免黑名单无限增长
            result = self.redis.setex(key, expires_in, json.dumps(revoke_data))
            
            if result:
                logger.info(f"Token {jti} 已加入黑名单，{expires_in}秒后过期")
            return bool(result)
            
        except Exception as e:
            logger.error(f"撤销token失败: {e}")
            return False
    
    def is_token_revoked(self, jti: str) -> bool:
        """
        检查token是否在黑名单中
        
        Args:
            jti: JWT ID
            
        Returns:
            bool: token是否被撤销
        """
        try:
            key = f"{self.prefix}{jti}"
            exists = self.redis.exists(key)
            return bool(exists)
        except Exception as e:
            logger.error(f"检查token黑名单状态失败: {e}")
            # 出错时保守处理，认为token有效
            return False
    
    def get_revoked_token_info(self, jti: str) -> Optional[Dict[str, Any]]:
        """获取被撤销token的详细信息"""
        try:
            key = f"{self.prefix}{jti}"
            data = self.redis.get(key)
            if data and isinstance(data, (str, bytes)):
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取撤销token信息失败: {e}")
            return None
    
    def cleanup_expired_tokens(self) -> int:
        """清理过期的黑名单token（Redis会自动处理，这里提供手动清理接口）"""
        try:
            # Redis的SETEX会自动过期，通常不需要手动清理
            # 这里提供一个获取当前黑名单大小的接口
            keys = self.redis.keys(f"{self.prefix}*")
            count = len(keys) if isinstance(keys, list) else 0
            logger.info(f"当前黑名单中有 {count} 个token")
            return count
        except Exception as e:
            logger.error(f"清理过期token失败: {e}")
            return 0

class SessionManager:
    """会话管理"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client.client
        self.prefix = "session:"
        self.default_ttl = 3600  # 1小时默认过期时间
    
    def create_session(self, user_id: str, session_data: Dict[str, Any], ttl: Optional[int] = None) -> Optional[str]:
        """
        创建用户会话
        
        Args:
            user_id: 用户ID
            session_data: 会话数据
            ttl: 过期时间（秒）
            
        Returns:
            str: 会话ID
        """
        try:
            session_id = f"sess_{user_id}_{datetime.utcnow().timestamp()}"
            key = f"{self.prefix}{session_id}"
            
            # 添加元数据
            session_data.update({
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            })
            
            ttl = ttl or self.default_ttl
            result = self.redis.setex(key, ttl, json.dumps(session_data))
            
            if result:
                logger.info(f"为用户 {user_id} 创建会话 {session_id}")
                return session_id
            return None
            
        except Exception as e:
            logger.error(f"创建会话失败: {e}")
            return None
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        try:
            key = f"{self.prefix}{session_id}"
            data = self.redis.get(key)
            if data and isinstance(data, (str, bytes)):
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
    
    def update_session(self, session_id: str, session_data: Dict[str, Any], extend_ttl: bool = True) -> bool:
        """更新会话数据"""
        try:
            key = f"{self.prefix}{session_id}"
            
            # 更新最后活动时间
            session_data["last_activity"] = datetime.utcnow().isoformat()
            
            if extend_ttl:
                # 延长过期时间
                result = self.redis.setex(key, self.default_ttl, json.dumps(session_data))
            else:
                result = self.redis.set(key, json.dumps(session_data), keepttl=True)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"更新会话失败: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        try:
            key = f"{self.prefix}{session_id}"
            result = self.redis.delete(key)
            if result:
                logger.info(f"会话 {session_id} 已删除")
            return bool(result)
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[str]:
        """获取用户的所有会话"""
        try:
            pattern = f"{self.prefix}sess_{user_id}_*"
            keys = self.redis.keys(pattern)
            if isinstance(keys, list):
                return [key.replace(self.prefix, '') for key in keys]
            return []
        except Exception as e:
            logger.error(f"获取用户会话失败: {e}")
            return []

class CSRFTokenManager:
    """CSRF Token管理"""
    
    def __init__(self, redis_client: RedisClient):
        self.redis = redis_client.client
        self.prefix = "csrf:"
        self.default_ttl = 86400  # 24小时
    
    def generate_csrf_token(self, user_id: str) -> Optional[str]:
        """为用户生成CSRF token"""
        import secrets
        try:
            token = secrets.token_hex(32)
            key = f"{self.prefix}{user_id}"
            
            result = self.redis.setex(key, self.default_ttl, token)
            if result:
                logger.info(f"为用户 {user_id} 生成CSRF token")
                return token
            return None
            
        except Exception as e:
            logger.error(f"生成CSRF token失败: {e}")
            return None
    
    def verify_csrf_token(self, user_id: str, token: str) -> bool:
        """验证CSRF token"""
        try:
            key = f"{self.prefix}{user_id}"
            stored_token = self.redis.get(key)
            return stored_token == token
        except Exception as e:
            logger.error(f"验证CSRF token失败: {e}")
            return False
    
    def refresh_csrf_token(self, user_id: str) -> Optional[str]:
        """刷新用户的CSRF token"""
        return self.generate_csrf_token(user_id)

# 全局Redis客户端实例
redis_client = RedisClient()
token_blacklist = TokenBlacklist(redis_client)
session_manager = SessionManager(redis_client)
csrf_manager = CSRFTokenManager(redis_client)

def get_redis_client() -> RedisClient:
    """获取Redis客户端实例"""
    return redis_client

def get_token_blacklist() -> TokenBlacklist:
    """获取Token黑名单管理器"""
    return token_blacklist

def get_session_manager() -> SessionManager:
    """获取会话管理器"""
    return session_manager

def get_csrf_manager() -> CSRFTokenManager:
    """获取CSRF管理器"""
    return csrf_manager

# 健康检查函数
def check_redis_health() -> Dict[str, Any]:
    """Redis健康检查"""
    try:
        client = get_redis_client()
        is_connected = client.is_connected()
        info = client.get_info() if is_connected else {}
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connected": is_connected,
            "redis_version": info.get("redis_version", "unknown"),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0)
        }
    except Exception as e:
        return {
            "status": "error",
            "connected": False,
            "error": str(e)
        }
