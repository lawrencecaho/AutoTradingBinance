#!/usr/bin/env python3
"""
AutoTradingBinance Project Setup
专注于包安装和依赖管理
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# setuptools 配置
setup(
    name="autotradingbinance",
    version="0.1.0",
    description="自动化交易系统，集成加密通信和密钥管理",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AutoTrading Team",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        # Web 框架
        "fastapi>=0.115.0",
        "uvicorn>=0.34.0",
        
        # 认证和安全
        "python-jose[cryptography]>=3.4.0",
        "passlib[bcrypt]>=1.7.4",
        "pyotp>=2.9.0",
        "cryptography>=44.0.0",
        
        # 数据处理
        "pydantic>=2.9.0",
        "python-multipart>=0.0.20",
        "python-dotenv>=1.1.0",
        
        # 数据库
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        
        # 交易相关
        "python-binance>=1.0.28",
        "requests>=2.32.0",
        
        # 数据分析
        "pandas>=2.2.0",
        "numpy>=2.2.0",
        
        # 工具库
        "python-dateutil>=2.9.0",
        "pytz>=2025.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "redis": [
            "redis>=6.2.0",
        ],
    },
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "autotrading-manage=manage:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="trading automation binance fastapi security",
    project_urls={
        "Bug Reports": "https://github.com/lawrencecaho/AutoTradingBinance/issues",
        "Source": "https://github.com/lawrencecaho/AutoTradingBinance",
    },
)
