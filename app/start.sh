#!/bin/bash
# app目录启动脚本

# 确保在app目录下
cd "$(dirname "${BASH_SOURCE[0]}")"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 AutoTradingBinance (App目录)${NC}"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 创建虚拟环境...${NC}"
    python3 -m venv venv
fi

# 激活虚拟环境
echo -e "${YELLOW}🔧 激活虚拟环境...${NC}"
source venv/bin/activate

# 安装依赖
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}📦 安装依赖...${NC}"
    pip install -r requirements.txt
fi

echo -e "${GREEN}✅ 环境准备完成${NC}"
echo "当前工作目录: $(pwd)"
echo ""
echo "可用命令："
echo "  python main.py                          - 运行主程序"
echo "  python -m uvicorn myfastapi.main:app --reload --port 8000  - 启动API服务"
echo "  python fetcher.py --store               - 运行数据获取器"
echo ""

# 保持在虚拟环境中
exec bash
