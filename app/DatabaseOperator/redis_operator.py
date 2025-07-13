# app/DatabaseOperator/redis_operator.py
"""
Redis 操作模块 - 专门用于交易相关的缓存操作
包含交易对管理、订单缓存、价格缓存等功能
"""
import os
import redis
import json
import logging
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal

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