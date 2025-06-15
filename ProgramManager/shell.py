#!/usr/bin/env python3
"""
AutoTradingBinance 项目管理器 - 交互式 Shell 界面
专业的项目管理和运维工具
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
PROGRAM_MANAGER_DIR = Path(__file__).parent

class Colors:
    """ANSI 颜色代码"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[0;37m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

class ProjectManagerShell:
    """AutoTradingBinance 项目管理器交互式界面"""
    
    def __init__(self):
        self.running = True
        self.history = []
        self.project_status = {}
        
    def print_colored(self, text, color=Colors.WHITE, bold=False):
        """打印彩色文本"""
        prefix = Colors.BOLD if bold else ""
        print(f"{prefix}{color}{text}{Colors.RESET}")
    
    def print_banner(self):
        """打印欢迎横幅"""
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                   AutoTradingBinance                         ║
║                   项目管理器 Shell 界面                      ║
║                                                              ║
║  🚀 专业的自动化交易系统管理工具                             ║
║  🔐 集成安全管理、依赖管理、系统监控                         ║
║  📊 实时状态监控和一键式操作                                 ║
╚══════════════════════════════════════════════════════════════╝
{Colors.RESET}

{Colors.GREEN}欢迎使用 AutoTradingBinance 项目管理器！{Colors.RESET}
{Colors.YELLOW}输入 'help' 查看可用命令，输入 'exit' 退出{Colors.RESET}
"""
        print(banner)
    
    def print_menu(self):
        """打印主菜单"""
        menu = f"""
{Colors.CYAN}{Colors.BOLD}┌─ 主菜单 ─┐{Colors.RESET}
{Colors.BLUE}│{Colors.RESET} {Colors.GREEN}1.{Colors.RESET} 项目设置     {Colors.BLUE}│{Colors.RESET} {Colors.YELLOW}setup{Colors.RESET}        - 完整环境设置
{Colors.BLUE}│{Colors.RESET} {Colors.GREEN}2.{Colors.RESET} 依赖管理     {Colors.BLUE}│{Colors.RESET} {Colors.YELLOW}deps{Colors.RESET}         - 依赖安装/更新  
{Colors.BLUE}│{Colors.RESET} {Colors.GREEN}3.{Colors.RESET} 安全管理     {Colors.BLUE}│{Colors.RESET} {Colors.YELLOW}security{Colors.RESET}     - 安全检查/权限设置
{Colors.BLUE}│{Colors.RESET} {Colors.GREEN}4.{Colors.RESET} 密钥管理     {Colors.BLUE}│{Colors.RESET} {Colors.YELLOW}keys{Colors.RESET}         - 密钥检查/轮换
{Colors.BLUE}│{Colors.RESET} {Colors.GREEN}5.{Colors.RESET} Redis管理    {Colors.BLUE}│{Colors.RESET} {Colors.YELLOW}redis{Colors.RESET}        - Redis连接/监控/测试
{Colors.BLUE}│{Colors.RESET} {Colors.GREEN}6.{Colors.RESET} 服务器管理   {Colors.BLUE}│{Colors.RESET} {Colors.YELLOW}server{Colors.RESET}       - 启动/停止服务器
{Colors.BLUE}│{Colors.RESET} {Colors.GREEN}7.{Colors.RESET} 系统监控     {Colors.BLUE}│{Colors.RESET} {Colors.YELLOW}monitor{Colors.RESET}      - 系统状态监控
{Colors.BLUE}│{Colors.RESET} {Colors.GREEN}8.{Colors.RESET} 项目状态     {Colors.BLUE}│{Colors.RESET} {Colors.YELLOW}status{Colors.RESET}       - 查看项目状态
{Colors.BLUE}│{Colors.RESET} {Colors.GREEN}9.{Colors.RESET} 日志查看     {Colors.BLUE}│{Colors.RESET} {Colors.YELLOW}logs{Colors.RESET}         - 查看系统日志
{Colors.BLUE}└─────────────┘{Colors.RESET}

{Colors.PURPLE}快捷命令:{Colors.RESET} {Colors.YELLOW}help{Colors.RESET}, {Colors.YELLOW}clear{Colors.RESET}, {Colors.YELLOW}history{Colors.RESET}, {Colors.YELLOW}exit{Colors.RESET}
"""
        print(menu)
    
    def run_command(self, command):
        """执行命令"""
        self.history.append(f"{datetime.now().strftime('%H:%M:%S')} - {command}")
        
        if command in ['exit', 'quit', 'q']:
            self.running = False
            self.print_colored("👋 感谢使用 AutoTradingBinance 项目管理器！", Colors.GREEN, bold=True)
            return
        
        elif command in ['help', 'h', '?']:
            self.print_menu()
            
        elif command in ['clear', 'cls']:
            os.system('clear' if os.name == 'posix' else 'cls')
            self.print_banner()
            
        elif command == 'history':
            self.show_history()
            
        elif command in ['1', 'setup']:
            self.setup_project()
            
        elif command in ['2', 'deps', 'dependencies']:
            self.manage_dependencies()
            
        elif command in ['3', 'security', 'sec']:
            self.manage_security()
            
        elif command in ['4', 'keys', 'key']:
            self.manage_keys()
            
        elif command in ['5', 'redis']:
            self.manage_redis()
            
        elif command in ['6', 'server', 'srv']:
            self.manage_server()
            
        elif command in ['7', 'monitor', 'mon']:
            self.system_monitor()
            
        elif command in ['8', 'status', 'stat']:
            self.show_status()
            
        elif command in ['9', 'logs', 'log']:
            self.show_logs()
            
        else:
            self.print_colored(f"❌ 未知命令: {command}", Colors.RED)
            self.print_colored("💡 输入 'help' 查看可用命令", Colors.YELLOW)
    
    def setup_project(self):
        """项目设置"""
        self.print_colored("\n🚀 项目完整设置", Colors.BLUE, bold=True)
        self.print_colored("这将执行：依赖安装 → 权限设置 → 安全检查 → 密钥验证", Colors.CYAN)
        
        confirm = input(f"{Colors.YELLOW}是否继续？(y/N): {Colors.RESET}")
        if confirm.lower() in ['y', 'yes']:
            self.run_manage_command('setup')
        else:
            self.print_colored("⏸️ 操作已取消", Colors.YELLOW)
    
    def manage_dependencies(self):
        """依赖管理"""
        self.print_colored("\n📦 依赖管理", Colors.BLUE, bold=True)
        deps_menu = f"""
{Colors.GREEN}1.{Colors.RESET} 安装依赖 (install)
{Colors.GREEN}2.{Colors.RESET} 更新依赖 (update)  
{Colors.GREEN}3.{Colors.RESET} 检查依赖 (check)
{Colors.GREEN}4.{Colors.RESET} 返回主菜单
"""
        print(deps_menu)
        
        choice = input(f"{Colors.YELLOW}请选择 (1-4): {Colors.RESET}")
        if choice == '1':
            self.run_manage_command('install')
        elif choice == '2':
            self.run_manage_command('update-deps')
        elif choice == '3':
            self.check_dependencies()
        elif choice == '4':
            return
        else:
            self.print_colored("❌ 无效选择", Colors.RED)
    
    def manage_security(self):
        """安全管理"""
        self.print_colored("\n🔐 安全管理", Colors.BLUE, bold=True)
        security_menu = f"""
{Colors.GREEN}1.{Colors.RESET} 安全检查 (security)
{Colors.GREEN}2.{Colors.RESET} 权限设置 (permissions)
{Colors.GREEN}3.{Colors.RESET} 系统检查 (system)
{Colors.GREEN}4.{Colors.RESET} 返回主菜单
"""
        print(security_menu)
        
        choice = input(f"{Colors.YELLOW}请选择 (1-4): {Colors.RESET}")
        if choice == '1':
            self.run_manage_command('security')
        elif choice == '2':
            self.run_manage_command('permissions')
        elif choice == '3':
            self.run_shell_script('check_system.sh', '系统环境检查')
        elif choice == '4':
            return
        else:
            self.print_colored("❌ 无效选择", Colors.RED)
    
    def manage_keys(self):
        """密钥管理"""
        self.print_colored("\n🔑 密钥管理", Colors.BLUE, bold=True)
        keys_menu = f"""
{Colors.GREEN}1.{Colors.RESET} 检查密钥状态
{Colors.GREEN}2.{Colors.RESET} 轮换密钥
{Colors.GREEN}3.{Colors.RESET} 生成新密钥
{Colors.GREEN}4.{Colors.RESET} 返回主菜单
"""
        print(keys_menu)
        
        choice = input(f"{Colors.YELLOW}请选择 (1-4): {Colors.RESET}")
        if choice == '1':
            self.run_manage_command('check-keys')
        elif choice == '2':
            self.rotate_keys()
        elif choice == '3':
            self.generate_keys()
        elif choice == '4':
            return
        else:
            self.print_colored("❌ 无效选择", Colors.RED)
    
    def manage_server(self):
        """服务器管理"""
        self.print_colored("\n🚀 服务器管理", Colors.BLUE, bold=True)
        server_menu = f"""
{Colors.GREEN}1.{Colors.RESET} 启动服务器
{Colors.GREEN}2.{Colors.RESET} 停止服务器
{Colors.GREEN}3.{Colors.RESET} 重启服务器
{Colors.GREEN}4.{Colors.RESET} 服务器状态
{Colors.GREEN}5.{Colors.RESET} 返回主菜单
"""
        print(server_menu)
        
        choice = input(f"{Colors.YELLOW}请选择 (1-5): {Colors.RESET}")
        if choice == '1':
            self.start_server()
        elif choice == '2':
            self.stop_server()
        elif choice == '3':
            self.restart_server()
        elif choice == '4':
            self.server_status()
        elif choice == '5':
            return
        else:
            self.print_colored("❌ 无效选择", Colors.RED)
    
    def system_monitor(self):
        """系统监控"""
        self.print_colored("\n📊 系统监控", Colors.BLUE, bold=True)
        
        try:
            # 添加项目路径
            sys.path.insert(0, str(PROJECT_ROOT))
            
            # 检查系统资源
            import psutil
            
            print(f"{Colors.CYAN}系统资源使用情况:{Colors.RESET}")
            print(f"CPU 使用率: {Colors.GREEN}{psutil.cpu_percent(interval=1):.1f}%{Colors.RESET}")
            print(f"内存使用率: {Colors.GREEN}{psutil.virtual_memory().percent:.1f}%{Colors.RESET}")
            print(f"磁盘使用率: {Colors.GREEN}{psutil.disk_usage('/').percent:.1f}%{Colors.RESET}")
            
            # 检查进程
            print(f"\n{Colors.CYAN}相关进程:{Colors.RESET}")
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower() and 'fastapi' in ' '.join(proc.info['cmdline'] or []):
                        print(f"🟢 FastAPI 进程: PID {proc.info['pid']}")
                except:
                    continue
                    
        except ImportError:
            self.print_colored("⚠️ psutil 未安装，无法显示系统监控", Colors.YELLOW)
        except Exception as e:
            self.print_colored(f"❌ 监控失败: {str(e)}", Colors.RED)
    
    def show_status(self):
        """显示项目状态"""
        self.print_colored("\n📋 项目状态概览", Colors.BLUE, bold=True)
        self.run_manage_command('status')
    
    def show_logs(self):
        """显示日志"""
        self.print_colored("\n📄 日志查看", Colors.BLUE, bold=True)
        
        log_files = [
            PROJECT_ROOT / "fastapi.log",
            PROJECT_ROOT / "myfastapi" / "fastapi.log"
        ]
        
        for log_file in log_files:
            if log_file.exists():
                print(f"\n{Colors.CYAN}📁 {log_file.name}:{Colors.RESET}")
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        # 显示最后20行
                        for line in lines[-20:]:
                            print(f"  {line.rstrip()}")
                except Exception as e:
                    self.print_colored(f"❌ 读取日志失败: {str(e)}", Colors.RED)
            else:
                print(f"\n{Colors.YELLOW}⚠️ 日志文件不存在: {log_file.name}{Colors.RESET}")
    
    def show_history(self):
        """显示命令历史"""
        self.print_colored("\n📚 命令历史", Colors.BLUE, bold=True)
        if self.history:
            for cmd in self.history[-10:]:  # 显示最近10条
                print(f"  {Colors.CYAN}{cmd}{Colors.RESET}")
        else:
            self.print_colored("暂无命令历史", Colors.YELLOW)
    
    def run_manage_command(self, command):
        """运行 manage.py 命令"""
        manage_script = PROGRAM_MANAGER_DIR / "manage.py"
        if manage_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(manage_script), command],
                    cwd=PROJECT_ROOT,
                    check=False
                )
                if result.returncode == 0:
                    self.print_colored(f"✅ 命令 '{command}' 执行成功", Colors.GREEN)
                else:
                    self.print_colored(f"⚠️ 命令 '{command}' 执行完成，但可能有问题", Colors.YELLOW)
            except Exception as e:
                self.print_colored(f"❌ 执行命令失败: {str(e)}", Colors.RED)
        else:
            self.print_colored("❌ 管理脚本不存在", Colors.RED)
    
    def run_shell_script(self, script_name, description):
        """运行 shell 脚本"""
        script_path = PROGRAM_MANAGER_DIR / script_name
        if script_path.exists():
            self.print_colored(f"\n🔧 {description}...", Colors.BLUE)
            try:
                result = subprocess.run(
                    ["bash", str(script_path)],
                    cwd=PROJECT_ROOT,
                    check=False
                )
                if result.returncode == 0:
                    self.print_colored(f"✅ {description} 完成", Colors.GREEN)
                else:
                    self.print_colored(f"⚠️ {description} 完成，但发现问题", Colors.YELLOW)
            except Exception as e:
                self.print_colored(f"❌ 执行失败: {str(e)}", Colors.RED)
        else:
            self.print_colored(f"⚠️ 脚本 {script_name} 不存在", Colors.YELLOW)
    
    def check_dependencies(self):
        """检查依赖状态"""
        self.print_colored("📦 检查 Python 依赖...", Colors.BLUE)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--outdated"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True
            )
            if result.stdout:
                print(f"{Colors.YELLOW}过期的包:{Colors.RESET}")
                print(result.stdout)
            else:
                self.print_colored("✅ 所有依赖都是最新的", Colors.GREEN)
        except Exception as e:
            self.print_colored(f"❌ 检查依赖失败: {str(e)}", Colors.RED)
    
    def rotate_keys(self):
        """轮换密钥"""
        self.print_colored("🔄 轮换密钥...", Colors.BLUE)
        confirm = input(f"{Colors.YELLOW}确认轮换所有密钥？(y/N): {Colors.RESET}")
        if confirm.lower() in ['y', 'yes']:
            try:
                # 添加项目路径
                sys.path.insert(0, str(PROJECT_ROOT))
                from myfastapi.security import force_regenerate_all_secrets
                force_regenerate_all_secrets()
                self.print_colored("✅ 密钥轮换完成", Colors.GREEN)
            except Exception as e:
                self.print_colored(f"❌ 密钥轮换失败: {str(e)}", Colors.RED)
        else:
            self.print_colored("⏸️ 操作已取消", Colors.YELLOW)
    
    def generate_keys(self):
        """生成新密钥"""
        self.print_colored("🔑 生成新密钥...", Colors.BLUE)
        # 这里可以调用密钥生成函数
        self.print_colored("💡 使用 '轮换密钥' 功能来生成新密钥", Colors.YELLOW)
    
    def start_server(self):
        """启动服务器"""
        self.print_colored("🚀 启动 FastAPI 服务器...", Colors.BLUE)
        self.print_colored("⚠️ 服务器将在后台启动，使用 Ctrl+C 返回主菜单", Colors.YELLOW)
        self.run_manage_command('server')
    
    def stop_server(self):
        """停止服务器"""
        self.print_colored("🛑 停止服务器...", Colors.BLUE)
        try:
            # 查找并停止 FastAPI 进程
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower() and 'fastapi' in ' '.join(proc.info['cmdline'] or []):
                        proc.terminate()
                        self.print_colored(f"✅ 已停止进程 PID {proc.info['pid']}", Colors.GREEN)
                        return
                except:
                    continue
            self.print_colored("⚠️ 未找到运行中的 FastAPI 服务器", Colors.YELLOW)
        except ImportError:
            self.print_colored("⚠️ 需要安装 psutil 来管理进程", Colors.YELLOW)
        except Exception as e:
            self.print_colored(f"❌ 停止服务器失败: {str(e)}", Colors.RED)
    
    def restart_server(self):
        """重启服务器"""
        self.print_colored("🔄 重启服务器...", Colors.BLUE)
        self.stop_server()
        time.sleep(2)
        self.start_server()
    
    def server_status(self):
        """检查服务器状态"""
        self.print_colored("📊 检查服务器状态...", Colors.BLUE)
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                self.print_colored("✅ 服务器运行正常", Colors.GREEN)
            else:
                self.print_colored(f"⚠️ 服务器响应异常: {response.status_code}", Colors.YELLOW)
        except ImportError:
            self.print_colored("⚠️ 需要安装 requests 来检查服务器状态", Colors.YELLOW)
        except Exception as e:
            # 处理连接错误等异常
            if "Connection" in str(e) or "connection" in str(e):
                self.print_colored("❌ 服务器未运行或无法连接", Colors.RED)
            else:
                self.print_colored(f"❌ 检查状态失败: {str(e)}", Colors.RED)
    
    def manage_redis(self):
        """Redis管理"""
        self.print_colored("\n🔗 Redis管理", Colors.BLUE, bold=True)
        redis_menu = f"""
{Colors.GREEN}1.{Colors.RESET} 查看Redis配置
{Colors.GREEN}2.{Colors.RESET} 测试Redis连接
{Colors.GREEN}3.{Colors.RESET} 运行完整测试
{Colors.GREEN}4.{Colors.RESET} Redis统计信息
{Colors.GREEN}5.{Colors.RESET} 实时监控Redis
{Colors.GREEN}6.{Colors.RESET} 清理过期数据
{Colors.GREEN}7.{Colors.RESET} 返回主菜单
"""
        print(redis_menu)
        
        choice = input(f"{Colors.YELLOW}请选择 (1-7): {Colors.RESET}")
        if choice == '1':
            self.redis_config()
        elif choice == '2':
            self.redis_test_connection()
        elif choice == '3':
            self.redis_full_test()
        elif choice == '4':
            self.redis_stats()
        elif choice == '5':
            self.redis_monitor()
        elif choice == '6':
            self.redis_cleanup()
        elif choice == '7':
            return
        else:
            self.print_colored("❌ 无效选择", Colors.RED)
    
    def redis_config(self):
        """显示Redis配置"""
        self.print_colored("\n📋 执行Redis配置查看...", Colors.CYAN)
        self.run_redis_command('config')
    
    def redis_test_connection(self):
        """测试Redis连接"""
        self.print_colored("\n🔄 测试Redis连接...", Colors.CYAN)
        self.run_redis_command('test')
    
    def redis_full_test(self):
        """运行完整Redis测试"""
        self.print_colored("\n🧪 运行完整Redis测试套件...", Colors.CYAN)
        self.run_redis_command('all')
    
    def redis_stats(self):
        """显示Redis统计信息"""
        self.print_colored("\n📊 获取Redis统计信息...", Colors.CYAN)
        self.run_redis_command('stats')
    
    def redis_monitor(self):
        """Redis实时监控"""
        self.print_colored("\n📡 启动Redis实时监控...", Colors.CYAN)
        self.print_colored("💡 按 Ctrl+C 停止监控", Colors.YELLOW)
        
        interval = input(f"{Colors.YELLOW}监控间隔(秒, 默认5): {Colors.RESET}") or "5"
        count = input(f"{Colors.YELLOW}监控次数(默认20): {Colors.RESET}") or "20"
        
        try:
            redis_script = PROGRAM_MANAGER_DIR / "redis_manager.py"
            if redis_script.exists():
                result = subprocess.run([
                    sys.executable, str(redis_script), 'monitor',
                    '--interval', interval, '--count', count
                ], cwd=PROJECT_ROOT, check=False)
                
                if result.returncode == 0:
                    self.print_colored("✅ Redis监控完成", Colors.GREEN)
                else:
                    self.print_colored("⚠️ Redis监控异常结束", Colors.YELLOW)
            else:
                self.print_colored("❌ Redis管理器脚本不存在", Colors.RED)
        except KeyboardInterrupt:
            self.print_colored("\n⏹️  监控已停止", Colors.YELLOW)
        except Exception as e:
            self.print_colored(f"❌ Redis监控失败: {e}", Colors.RED)
    
    def redis_cleanup(self):
        """清理Redis过期数据"""
        self.print_colored("\n🧹 清理Redis过期数据...", Colors.CYAN)
        self.run_redis_command('cleanup')
    
    def run_redis_command(self, action):
        """运行Redis管理器命令"""
        redis_script = PROGRAM_MANAGER_DIR / "redis_manager.py"
        if redis_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(redis_script), action],
                    cwd=PROJECT_ROOT,
                    check=False
                )
                if result.returncode == 0:
                    self.print_colored(f"✅ Redis命令 '{action}' 执行成功", Colors.GREEN)
                else:
                    self.print_colored(f"⚠️ Redis命令 '{action}' 执行完成，但可能有问题", Colors.YELLOW)
            except Exception as e:
                self.print_colored(f"❌ Redis命令执行失败: {str(e)}", Colors.RED)
        else:
            self.print_colored("❌ Redis管理器脚本不存在", Colors.RED)

    # ...existing code...
    
    def run(self):
        """运行交互式界面"""
        try:
            self.print_banner()
            self.print_menu()
            
            while self.running:
                try:
                    # 显示提示符
                    prompt = f"{Colors.BLUE}[AutoTrading]{Colors.YELLOW}➤{Colors.RESET} "
                    command = input(prompt).strip().lower()
                    
                    if command:
                        self.run_command(command)
                        print()  # 空行分隔
                        
                except KeyboardInterrupt:
                    print()
                    self.print_colored("👋 感谢使用 AutoTradingBinance 项目管理器！", Colors.GREEN, bold=True)
                    break
                except EOFError:
                    print()
                    break
                    
        except Exception as e:
            self.print_colored(f"❌ 程序异常: {str(e)}", Colors.RED)

def main():
    """主函数"""
    shell = ProjectManagerShell()
    shell.run()

if __name__ == "__main__":
    main()
