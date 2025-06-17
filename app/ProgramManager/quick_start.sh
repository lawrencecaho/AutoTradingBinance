#!/bin/bash
# quick_start.sh
# 快速启动脚本，用于设置开发环境并运行服务

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}====== 自动交易系统快速启动 ======${NC}\n"

# 获取项目根目录
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT" || exit 1

# 创建测试用户
echo -e "${YELLOW}1. 创建测试用户...${NC}"
python myfastapi/create_test_user.py --uid testuser --username "测试用户"
echo

# 启动API服务器
echo -e "${YELLOW}2. 启动API服务器...${NC}"
echo -e "${GREEN}在新的终端窗口中运行以下命令:${NC}"
echo -e "cd \"$PROJECT_ROOT\" && uvicorn myfastapi.main:app --reload"
echo

# 启动前端
echo -e "${YELLOW}3. 启动前端开发服务器...${NC}"
echo -e "${GREEN}在另一个新的终端窗口中运行以下命令:${NC}"
echo -e "cd \"$PROJECT_ROOT/Frontend\" && npm run dev"
echo

echo -e "${YELLOW}====== 访问应用 ======${NC}"
echo -e "前端: ${GREEN}http://localhost:3000/login${NC}"
echo -e "API文档: ${GREEN}http://localhost:8000/docs${NC}"
echo

echo -e "${YELLOW}====== 测试指南 ======${NC}"
echo -e "运行测试套件: ${GREEN}bash myfastapi/run_tests.sh${NC}"
echo -e "查看详细测试文档: ${GREEN}docs/testing_guide.md${NC}"
echo

echo -e "${YELLOW}====== 登录信息 ======${NC}"
echo -e "用户ID: ${GREEN}testuser${NC}"
echo -e "验证码: 使用Google Authenticator扫描生成的二维码获取"
echo

echo -e "${YELLOW}完成! 系统准备就绪。${NC}"
