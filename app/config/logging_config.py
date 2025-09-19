# app/config/logging_config.py
"""
统一的日志配置模块
为整个项目提供一致的日志配置
"""

import os
import logging
import logging.config
from pathlib import Path
from typing import Dict, Any, Optional


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def get_logs_dir() -> Path:
    """获取日志目录，不存在则创建"""
    logs_dir = get_project_root() / "logs"
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def get_log_file_path(filename: str) -> str:
    """获取日志文件的完整路径"""
    return str(get_logs_dir() / filename)


def get_log_level() -> str:
    """从环境变量获取日志级别，默认为INFO"""
    return os.getenv('LOG_LEVEL', 'INFO').upper()


def is_development() -> bool:
    """判断是否为开发环境"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    return env in ['development', 'dev', 'local']


# 项目统一日志配置
def get_logging_config() -> Dict[str, Any]:
    """
    动态生成日志配置，支持环境变量控制
    """
    log_level = get_log_level()
    is_dev = is_development()
    
    # 开发环境显示更详细的日志格式
    detailed_format = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s" if is_dev else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        
        "formatters": {
            "detailed": {
                "format": detailed_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "format": "%(asctime)s - %(levelname)s - %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "console": {
                "format": "%(levelname)s - %(name)s - %(message)s",
            },
            "uvicorn_default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(message)s",
                "use_colors": None,
            },
        },
        
        "handlers": {
            # 控制台输出
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG" if is_dev else "INFO",
                "formatter": "console",
                "stream": "ext://sys.stdout",
            },
            
            # 应用主日志文件
            "app_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": get_log_file_path("app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            
            # 错误日志文件
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": get_log_file_path("error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            
            # 交易数据日志
            "trading_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": get_log_file_path("trading.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf-8",
            },
            
            # WebSocket 数据日志
            "websocket_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": get_log_file_path("websocket.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            
            # FastAPI 专用
            "fastapi_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": get_log_file_path("fastapi.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        
        "loggers": {
            # 核心业务模块
            "ExchangeFetcher": {
                "handlers": ["console", "trading_file", "websocket_file"],
                "level": "DEBUG" if is_dev else "INFO",
                "propagate": False,
            },
            
            "DatabaseOperator": {
                "handlers": ["console", "app_file"],
                "level": log_level,
                "propagate": False,
            },
            
            "DataProcessingCalculator": {
                "handlers": ["console", "trading_file"],
                "level": log_level,
                "propagate": False,
            },
            
            "WorkLine": {
                "handlers": ["console", "app_file"],
                "level": log_level,
                "propagate": False,
            },
            
            # FastAPI 相关
            "myfastapi": {
                "handlers": ["console", "fastapi_file"],
                "level": "DEBUG" if is_dev else "INFO",
                "propagate": False,
            },
            
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            
            "uvicorn.error": {
                "handlers": ["console", "error_file"],
                "level": "INFO",
                "propagate": False,
            },
            
            "uvicorn.access": {
                "handlers": ["fastapi_file"],
                "level": "INFO",
                "propagate": False,
            },
            
            # 特定脚本
            "__main__": {
                "handlers": ["console", "app_file"],
                "level": "DEBUG" if is_dev else log_level,
                "propagate": False,
            },
        },
        
        "root": {
            "handlers": ["console", "app_file", "error_file"],
            "level": log_level,
        },
    }
    
    return config


# 获取配置（向后兼容）
PROJECT_LOGGING_CONFIG = get_logging_config()


def setup_logging(config_dict: Optional[Dict[str, Any]] = None) -> None:
    """
    设置项目日志配置
    
    Args:
        config_dict: 自定义配置字典，如果为None则使用默认配置
    """
    if config_dict is None:
        config_dict = get_logging_config()
    
    # 确保日志目录存在
    get_logs_dir()
    
    # 应用配置
    logging.config.dictConfig(config_dict)
    
    # 输出配置信息
    logger = logging.getLogger(__name__)
    env = os.getenv('ENVIRONMENT', 'development')
    log_level = get_log_level()
    logger.info(f"日志系统已初始化 - 环境: {env}, 级别: {log_level}")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称，默认为调用模块的 __name__
    
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    if name is None:
        # 获取调用者的模块名
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'unknown')
        else:
            name = 'unknown'
    
    return logging.getLogger(name)


def get_trading_logger() -> logging.Logger:
    """获取交易专用日志记录器"""
    return logging.getLogger("trading")


def get_websocket_logger() -> logging.Logger:
    """获取WebSocket专用日志记录器"""
    return logging.getLogger("websocket")


# 为了兼容性，提供快速设置函数
def quick_setup() -> None:
    """快速设置日志，适用于简单脚本"""
    setup_logging()


if __name__ == "__main__":
    # 测试日志配置
    setup_logging()
    
    # 测试各种日志记录器
    main_logger = get_logger(__name__)
    trading_logger = get_trading_logger()
    websocket_logger = get_websocket_logger()
    
    main_logger.info("主应用日志测试")
    main_logger.error("错误日志测试")
    trading_logger.info("交易日志测试")
    websocket_logger.debug("WebSocket调试日志测试")
    
    print("日志配置测试完成，请检查 logs/ 目录中的日志文件")