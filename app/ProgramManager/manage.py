#!/usr/bin/env python3
"""
AutoTradingBinance 项目管理工具
集成项目依赖管理、安全配置和环境设置
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# 项目根目录（ProgramManager 的父目录）
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def print_colored(text, color="white"):
    """打印彩色文本"""
    colors = {
        "green": "\033[0;32m",
        "red": "\033[0;31m", 
        "yellow": "\033[0;33m",
        "blue": "\033[0;34m",
        "white": "\033[0;37m",
        "reset": "\033[0m"
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def run_script(script_name, description):
    """运行shell脚本"""
    # 脚本在 ProgramManager 目录中
    script_path = Path(__file__).parent / script_name
    if script_path.exists():
        print_colored(f"\n🔧 {description}...", "blue")
        try:
            result = subprocess.run(
                ["bash", str(script_path)], 
                cwd=PROJECT_ROOT,  # 但在项目根目录运行
                check=False
            )
            if result.returncode == 0:
                print_colored(f"✅ {description} 完成", "green")
                return True
            else:
                print_colored(f"⚠️ {description} 完成，但发现一些问题 (退出码: {result.returncode})", "yellow")
                return False
        except Exception as e:
            print_colored(f"❌ 运行 {script_name} 失败: {str(e)}", "red")
            return False
    else:
        print_colored(f"⚠️ 脚本 {script_name} 不存在，跳过", "yellow")
        return True

def setup_environment():
    """设置项目环境"""
    print_colored("🚀 开始设置 AutoTradingBinance 项目环境", "blue")
    
    success_count = 0
    total_steps = 4
    
    # 1. 更新依赖
    if run_script("update_deps.sh", "更新项目依赖"):
        success_count += 1
    
    # 2. 设置安全权限
    if run_script("secure_permissions.sh", "设置文件安全权限"):
        success_count += 1
    
    # 3. 运行安全检查
    if run_script("security_check.sh", "运行安全检查"):
        success_count += 1
    
    # 4. 系统检查
    if run_script("check_system.sh", "系统环境检查"):
        success_count += 1
    
    print_colored(f"\n📊 环境设置完成！({success_count}/{total_steps} 步骤成功)", "green")
    
    if success_count == total_steps:
        print_colored("🎉 所有步骤都成功完成！", "green")
    else:
        print_colored("⚠️ 部分步骤有问题，请查看上述输出", "yellow")

def install_dependencies():
    """安装Python依赖"""
    print_colored("📦 安装Python依赖包...", "blue")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                      cwd=PROJECT_ROOT, check=True)
        print_colored("✅ Python依赖安装完成", "green")
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ 依赖安装失败: {str(e)}", "red")
        return False

def check_key_management():
    """检查密钥管理系统"""
    print_colored("🔐 检查密钥管理系统...", "blue")
    try:
        # 添加项目路径
        sys.path.insert(0, str(PROJECT_ROOT))
        
        from myfastapi.security import get_all_secrets_info
        
        info = get_all_secrets_info()
        print_colored("密钥管理系统状态:", "white")
        
        for key, value in info.items():
            if key == 'validity_days':
                print_colored(f"  轮换周期: {value} 天", "white")
            elif isinstance(value, dict):
                status = "✅ 有效" if not value.get('expired', True) else "❌ 过期"
                days = value.get('expires_in_days', 0)
                print_colored(f"  {key}: {status} (剩余 {days} 天)", "white")
        
        print_colored("✅ 密钥管理系统正常", "green")
        return True
        
    except Exception as e:
        print_colored(f"❌ 密钥管理系统检查失败: {str(e)}", "red")
        return False

def start_server():
    """启动 FastAPI 服务器"""
    print_colored("🚀 启动 FastAPI 服务器...", "blue")
    try:
        # 添加项目路径到 sys.path
        sys.path.insert(0, str(PROJECT_ROOT))
        
        import uvicorn
        from myfastapi.main import app
        
        print_colored("✅ 应用加载成功，启动服务器...", "green")
        uvicorn.run(
            "myfastapi.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError as e:
        print_colored(f"❌ 导入错误: {str(e)}", "red")
        print_colored("💡 提示: 请确保运行 'python3 manage.py install' 安装依赖", "yellow")
    except Exception as e:
        print_colored(f"❌ 服务器启动失败: {str(e)}", "red")
    except KeyboardInterrupt:
        print_colored("\n🛑 服务器已停止", "yellow")

def show_status():
    """显示项目状态"""
    print_colored("📋 AutoTradingBinance 项目状态", "blue")
    
    # 检查重要文件
    important_files = [
        ("config.py", "配置文件"),
        ("myfastapi/security.py", "密钥管理"),
        ("myfastapi/main.py", "FastAPI应用"),
        (".env", "环境变量"),
        ("requirements.txt", "依赖清单")
    ]
    
    print_colored("\n📁 重要文件检查:", "blue")
    for file_path, description in important_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            print_colored(f"  ✅ {description}: {file_path}", "green")
        else:
            print_colored(f"  ❌ {description}: {file_path} (缺失)", "red")
    
    # 检查密钥系统
    print_colored("\n🔐 密钥系统状态:", "blue")
    check_key_management()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AutoTradingBinance 项目管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
常用命令示例:
  python3 manage.py setup         # 完整环境设置
  python3 manage.py install       # 仅安装依赖
  python3 manage.py server        # 启动服务器
  python3 manage.py status        # 查看项目状态
  python3 manage.py security      # 运行安全检查
        """
    )
    
    parser.add_argument("command", 
                       choices=["setup", "install", "security", "permissions", "check-keys", "update-deps", "server", "status"],
                       help="要执行的命令")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        print_colored("🎯 执行完整项目设置", "blue")
        install_dependencies()
        setup_environment()
        check_key_management()
        
    elif args.command == "install":
        install_dependencies()
        
    elif args.command == "security":
        run_script("security_check.sh", "安全检查")
        
    elif args.command == "permissions":
        run_script("secure_permissions.sh", "文件权限设置")
        
    elif args.command == "check-keys":
        check_key_management()
        
    elif args.command == "update-deps":
        run_script("update_deps.sh", "更新项目依赖")
        
    elif args.command == "server":
        start_server()
        
    elif args.command == "status":
        show_status()

if __name__ == "__main__":
    main()
