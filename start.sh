#!/bin/bash
# 启动脚本 - 在app目录下运行

# 获取脚本所在目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$PROJECT_ROOT/app"
cd "$APP_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 AutoTradingBinance 项目启动器${NC}"
echo "项目根目录: $PROJECT_ROOT"
echo "工作目录: $APP_DIR"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ 虚拟环境不存在，请先运行：python3 -m venv venv${NC}"
    exit 1
fi

# 激活虚拟环境
echo -e "${YELLOW}🔧 激活虚拟环境...${NC}"
source venv/bin/activate

# 检查依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}📦 安装依赖...${NC}"
    pip install -r ../requirements.txt
fi

echo -e "${GREEN}✅ 环境准备完成${NC}"
echo ""
echo "可用命令："
echo "  1. python main.py                                    - 运行主程序"
echo "  2. python -m uvicorn myfastapi.main:app --reload --port 8000  - 启动API服务"
echo "  3. python fetcher.py --store                         - 独立运行数据获取器"
echo "  4. cd ProgramManager && python manage.py             - 项目管理工具"
echo "  5. cd ProgramManager && python shell.py              - 交互式管理界面"
echo ""
echo -e "${YELLOW}当前在app目录的虚拟环境中，使用 'deactivate' 退出${NC}"

# 保持在虚拟环境中
exec bash
