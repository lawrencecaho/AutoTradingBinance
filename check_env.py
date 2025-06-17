#!/usr/bin/env python3
"""
环境检查脚本
检查项目的各种依赖和配置是否正确
"""

import sys
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent
APP_DIR = PROJECT_ROOT / "app"

# 添加app目录到Python路径
sys.path.insert(0, str(APP_DIR))

def print_status(check_name, status, message=""):
    """打印检查状态"""
    status_icon = "✅" if status else "❌"
    print(f"{status_icon} {check_name}: {message}")
    return status

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    is_ok = version.major == 3 and version.minor >= 9
    return print_status(
        "Python版本", 
        is_ok, 
        f"{version.major}.{version.minor}.{version.micro} {'(推荐)' if is_ok else '(需要3.9+)'}"
    )

def check_virtual_env():
    """检查是否在虚拟环境中"""
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    return print_status("虚拟环境", in_venv, "已激活" if in_venv else "未激活")

def check_core_imports():
    """检查核心模块导入"""
    modules = [
        ("fastapi", "FastAPI框架"),
        ("uvicorn", "ASGI服务器"),
        ("sqlalchemy", "数据库ORM"),
        ("psycopg2", "PostgreSQL驱动"),
        ("pandas", "数据分析"),
        ("requests", "HTTP客户端"),
        ("cryptography", "加密库"),
        ("redis", "Redis客户端")
    ]
    
    all_ok = True
    for module, desc in modules:
        try:
            __import__(module)
            print_status(f"模块 {module}", True, desc)
        except ImportError:
            print_status(f"模块 {module}", False, f"{desc} - 未安装")
            all_ok = False
    
    return all_ok

def check_project_modules():
    """检查项目模块"""
    modules = [
        ("config", "配置模块"),
        ("database", "数据库模块"),
        ("fetcher", "数据获取模块"),
        ("strategy", "交易策略模块"),
        ("myfastapi.main", "FastAPI主模块")
    ]
    
    all_ok = True
    for module, desc in modules:
        try:
            __import__(module)
            print_status(f"项目模块 {module}", True, desc)
        except ImportError as e:
            print_status(f"项目模块 {module}", False, f"{desc} - {str(e)}")
            all_ok = False
    
    return all_ok

def check_file_structure():
    """检查文件结构"""
    required_files = [
        ("app/config.py", "配置文件"),
        ("app/main.py", "主程序"),
        ("app/myfastapi/main.py", "FastAPI主文件"),
        ("Secret", "密钥目录"),
        ("app/venv", "虚拟环境目录"),
        ("requirements.txt", "依赖文件")
    ]
    
    all_ok = True
    for file_path, desc in required_files:
        full_path = PROJECT_ROOT / file_path
        exists = full_path.exists()
        print_status(f"文件/目录 {file_path}", exists, desc)
        if not exists:
            all_ok = False
    
    return all_ok

def main():
    """主检查函数"""
    print("🔍 AutoTradingBinance 环境检查")
    print(f"项目根目录: {PROJECT_ROOT}")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("虚拟环境", check_virtual_env),
        ("文件结构", check_file_structure),
        ("核心依赖", check_core_imports),
        ("项目模块", check_project_modules)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n📋 检查 {check_name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有检查通过！环境配置正确。")
        print("\n🚀 可以开始使用:")
        print("   ./start.sh                    - 启动开发环境")
        print("   cd app && python main.py      - 运行主程序")
        print("   cd app && uvicorn myfastapi.main:app --reload - 启动API服务")
    else:
        print("⚠️  发现问题，请根据上述提示修复后重试。")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
