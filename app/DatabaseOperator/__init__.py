# DatabaseOperator Initialization
"""
数据库模块
PostergreSQL 操作
Redis 操作
"""

# 延迟导入，避免在包级别导入时出现依赖错误
def init_db(*args, **kwargs):
    from .pg_operator import init_db as _init_db
    return _init_db(*args, **kwargs)

def get_session():
    from .pg_operator import Session
    return Session

# 提供直接访问模块的方式
def get_pg_operator():
    from . import pg_operator
    return pg_operator

def get_redis_operator():
    from . import redis_operator  
    return redis_operator

def get_trading_cache():
    from .redis_operator import trading_cache
    return trading_cache

# 为了保持向后兼容，提供 Session 属性
class _SessionProxy:
    def __getattr__(self, name):
        from .pg_operator import Session
        return getattr(Session, name)
    
    def __call__(self, *args, **kwargs):
        from .pg_operator import Session
        return Session(*args, **kwargs)

Session = _SessionProxy()

__all__ = ['init_db', 'Session', 'get_session', 'get_pg_operator', 'get_redis_operator', 'get_trading_cache']