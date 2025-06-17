#!/usr/bin/env python3
"""
AutoTradingBinance 项目管理器 - 快速启动入口
"""

import sys
import subprocess
from pathlib import Path

def main():
    """启动交互式 shell 界面"""
    # 获取项目根目录
    project_root = Path(__file__).parent.absolute()
    shell_script = project_root / "ProgramManager" / "shell.py"
    
    if shell_script.exists():
        try:
            # 直接运行 shell.py 脚本
            subprocess.run([sys.executable, str(shell_script)], cwd=project_root)
        except KeyboardInterrupt:
            print("\n👋 再见！")
        except Exception as e:
            print(f"❌ 启动失败: {e}")
    else:
        print("❌ 找不到 ProgramManager/shell.py")
        print("💡 请确保项目结构完整")

if __name__ == "__main__":
    main()
