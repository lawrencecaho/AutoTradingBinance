# app/config/__init__.py
"""
配置模块
包含项目的各种配置文件
"""

from .logging_config import (
    setup_logging,
    get_logger,
    get_trading_logger,
    get_websocket_logger,
    quick_setup,
    PROJECT_LOGGING_CONFIG
)

from .basicConfig import (
    BINANCE_API_BASE_URL, 
    DEFAULT_SYMBOL,
    DATABASE_URL,
    REDIS_URL,
    REDIS_PASSWORD,
    REDIS_DB,
    SYMBOL,
    FETCH_INTERVAL_SECONDS
)

__all__ = [
    # 日志配置
    'setup_logging',
    'get_logger', 
    'get_trading_logger',
    'get_websocket_logger',
    'PROJECT_LOGGING_CONFIG',
    'quick_setup',
    # 基础配置
    'BINANCE_API_BASE_URL',
    'DEFAULT_SYMBOL',
    'DATABASE_URL',
    'REDIS_URL',
    'REDIS_PASSWORD',
    'REDIS_DB',
    'SYMBOL',
    'FETCH_INTERVAL_SECONDS'
]