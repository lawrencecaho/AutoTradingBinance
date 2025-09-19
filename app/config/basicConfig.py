# config.py
"""
应用配置模块 - 仅包含配置变量，不包含业务逻辑
"""

import os
from dotenv import load_dotenv
from PathUniti import PROJECT_ROOT, get_secret_file

# 加载环境变量
load_dotenv()

# =============================================================================
# 基础配置
# =============================================================================

# 默认交易对
DEFAULT_SYMBOL = os.getenv('DEFAULT_SYMBOL', 'ETHUSDT')

# API配置
BINANCE_API_BASE_URL = os.getenv('BINANCE_API_BASE_URL', 'https://api.binance.com/api/v3/')

# 测试用 API 密钥 (生产环境应从环境变量获取)
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', 'PqG0U5YaArRtRKFPzXXS3AWnBX817uSpYnMIluDkG0RyDVVcphhtUsvLgw46MtJH')

# 私钥文件路径
BINANCE_PRIVATE_KEY_PATH = get_secret_file('Binance-testnet-prvke.pem')

# =============================================================================
# 数据库配置
# =============================================================================

DATABASE_URL = os.getenv(
    'DATABASE_URL', 
    "postgresql+psycopg2://postgres:hejiaye%402006@192.168.1.20:5432/trading"
)

# =============================================================================
# 应用配置
# =============================================================================

# 价格获取间隔（秒）
FETCH_INTERVAL_SECONDS = int(os.getenv('FETCH_INTERVAL_SECONDS', '6'))

# 日志级别
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# =============================================================================
# Redis 配置
# =============================================================================

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
REDIS_DB = int(os.getenv('REDIS_DB', '0'))

# =============================================================================
# 向后兼容 (待移除)
# =============================================================================

# 保留旧的变量名以确保现有代码不会立即崩溃
SYMBOL = DEFAULT_SYMBOL
StableUrl = BINANCE_API_BASE_URL





