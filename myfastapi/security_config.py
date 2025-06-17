# /myfastapi/security_config.py
"""
安全配置管理模块
根据环境变量动态配置安全参数
"""
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SecurityConfig:
    """安全配置管理类"""
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development').lower()
        self.is_production = self.environment == 'production'
        self.use_https = os.getenv('USE_HTTPS', 'false').lower() == 'true'
        
        # 验证生产环境必需配置
        if self.is_production:
            self._validate_production_config()
    
    def _validate_production_config(self):
        """验证生产环境必需的配置"""
        required_vars = ['COOKIE_DOMAIN', 'JWT_SECRET', 'DATABASE_URL', 'BINANCE_API_KEY', 'BINANCE_SECRET_KEY']
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value or (var == 'JWT_SECRET' and value == 'dev-jwt-secret-key-not-for-production'):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"生产环境缺少必需的环境变量或使用了开发环境的值: {', '.join(missing_vars)}")
            raise ValueError(f"生产环境缺少必需的环境变量: {', '.join(missing_vars)}")
        
        if not self.use_https:
            logger.warning("生产环境强烈建议启用HTTPS (USE_HTTPS=true)")
        
        # 检查Binance测试网配置
        if os.getenv('BINANCE_TESTNET', 'true').lower() == 'true':
            logger.warning("生产环境检测到BINANCE_TESTNET=true，请确认是否正确")
    
    def get_cookie_config(self, max_age: Optional[int] = None) -> Dict[str, Any]:
        """获取Cookie安全配置"""
        config = {
            'httponly': True,
            'secure': self.is_production or self.use_https,
            'samesite': 'strict' if self.is_production else 'lax',
            'path': '/',
        }
        
        # 生产环境设置域名
        if self.is_production:
            domain = os.getenv('COOKIE_DOMAIN')
            if domain:
                config['domain'] = domain
        
        # 设置过期时间
        if max_age is not None:
            config['max_age'] = max_age
        
        return config
    
    def get_jwt_config(self) -> Dict[str, Any]:
        """获取JWT配置"""
        return {
            'expire_minutes': int(os.getenv('JWT_EXPIRE_MINUTES', '15')),
            'algorithm': 'HS256',
            'issuer': 'AutoTradingBinance',
            'audience': 'web-client'
        }
    
    def get_csrf_config(self) -> Dict[str, Any]:
        """获取CSRF配置"""
        return {
            'expire_seconds': int(os.getenv('CSRF_EXPIRE_SECONDS', '1800')),
            'token_length': 32,
            'require_origin_check': self.is_production
        }
    
    def get_rate_limit_config(self) -> Dict[str, Any]:
        """获取速率限制配置"""
        return {
            'requests': int(os.getenv('RATE_LIMIT_REQUESTS', '100')),
            'window': int(os.getenv('RATE_LIMIT_WINDOW', '60'))
        }
    
    def get_cors_config(self) -> Dict[str, Any]:
        """获取CORS配置"""
        origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8000')
        return {
            'allow_origins': [origin.strip() for origin in origins.split(',') if origin.strip()],
            'allow_credentials': True,
            'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': ['*']
        }
    
    def get_timestamp_window(self) -> int:
        """获取时间戳验证窗口（毫秒）"""
        # 生产环境使用更严格的时间窗口
        return 30000 if self.is_production else 60000
    
    def should_log_unsigned_requests(self) -> bool:
        """是否记录未签名请求"""
        return True
    
    def get_security_headers(self) -> Dict[str, str]:
        """获取安全响应头"""
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        
        if self.is_production:
            headers.update({
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
            })
        
        return headers
    
    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return {
            'host': os.getenv('SERVER_HOST', '127.0.0.1'),
            'port': int(os.getenv('SERVER_PORT', '8000')),
            'timezone': os.getenv('TIMEZONE', 'Asia/Shanghai')
        }
    
    def get_binance_config(self) -> Dict[str, Any]:
        """获取Binance API配置"""
        return {
            'api_key': os.getenv('BINANCE_API_KEY', ''),
            'secret_key': os.getenv('BINANCE_SECRET_KEY', ''),
            'testnet': os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            'url': os.getenv('DATABASE_URL', ''),
            'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20'))
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置"""
        return {
            'url': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            'password': os.getenv('REDIS_PASSWORD', ''),
            'db': int(os.getenv('REDIS_DB', '0'))
        }

# 全局安全配置实例
security_config = SecurityConfig()

def get_security_config() -> SecurityConfig:
    """获取安全配置实例"""
    return security_config
