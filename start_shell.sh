#!/bin/bash

# AutoTradingBinance 项目管理器启动脚本
# 快速启动交互式管理界面

echo "🚀 启动 AutoTradingBinance 项目管理器..."

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装或不在 PATH 中"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

# 启动交互式 shell
python3 ProgramManager/shell.py
