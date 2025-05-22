#!/bin/bash
# check_system.sh - 系统检查和环境验证

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== 系统检查 =====${NC}"

# 保存当前目录
CURRENT_DIR=$(pwd)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 确保在项目根目录中
cd "$PROJECT_ROOT" || exit 1

# 检查Python版本
echo -e "${YELLOW}1. 检查Python版本${NC}"
PYTHON_VERSION=$(python --version 2>&1)
PYTHON_VERSION_NUM=$(echo $PYTHON_VERSION | sed 's/[^0-9.]//g')
PYTHON_MAJOR=$(echo $PYTHON_VERSION_NUM | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION_NUM | cut -d. -f2)

echo "当前Python版本: $PYTHON_VERSION"
if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 8 ]; then
    echo -e "${GREEN}✓ Python版本满足要求 (3.8+)${NC}"
else
    echo -e "${RED}✗ Python版本不满足要求，请安装Python 3.8或更高版本${NC}"
fi

# 检查pip
echo -e "\n${YELLOW}2. 检查pip${NC}"
if command -v pip &> /dev/null; then
    PIP_VERSION=$(pip --version)
    echo -e "${GREEN}✓ pip已安装: $PIP_VERSION${NC}"
else
    echo -e "${RED}✗ pip未安装${NC}"
fi

# 检查Node.js
echo -e "\n${YELLOW}3. 检查Node.js${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js已安装: $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js未安装，前端开发需要安装Node.js${NC}"
fi

# 检查npm
echo -e "\n${YELLOW}4. 检查npm${NC}"
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm已安装: $NPM_VERSION${NC}"
else
    echo -e "${RED}✗ npm未安装${NC}"
fi

# 检查PostgreSQL
echo -e "\n${YELLOW}5. 检查PostgreSQL${NC}"
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version)
    echo -e "${GREEN}✓ PostgreSQL已安装: $PSQL_VERSION${NC}"
else
    echo -e "${RED}✗ PostgreSQL未安装或未在PATH中${NC}"
fi

# 检查依赖
echo -e "\n${YELLOW}6. 检查Python依赖${NC}"
if [ -f "requirements.txt" ]; then
    MISSING_DEPS=$(pip freeze | sort | comm -23 <(sort requirements.txt) -)
    if [ -z "$MISSING_DEPS" ]; then
        echo -e "${GREEN}✓ 所有Python依赖已安装${NC}"
    else
        echo -e "${RED}✗ 缺少以下Python依赖:${NC}"
        echo "$MISSING_DEPS"
        echo -e "运行 ${YELLOW}pip install -r requirements.txt${NC} 安装缺少的依赖"
    fi
else
    echo -e "${RED}✗ 未找到requirements.txt文件${NC}"
fi

# 检查前端依赖
echo -e "\n${YELLOW}7. 检查前端依赖${NC}"
if [ -d "Frontend" ] && [ -f "Frontend/package.json" ]; then
    if [ -d "Frontend/node_modules" ]; then
        echo -e "${GREEN}✓ 前端依赖已安装${NC}"
    else
        echo -e "${RED}✗ 前端依赖未安装${NC}"
        echo -e "进入Frontend目录，运行 ${YELLOW}npm install${NC} 安装依赖"
    fi
else
    echo -e "${YELLOW}? 未找到前端项目或package.json文件${NC}"
fi

# 检查环境变量
echo -e "\n${YELLOW}8. 检查环境变量${NC}"
REQUIRED_ENV_VARS=("DATABASE_URL" "JWT_SECRET" "API_SECRET_KEY")
MISSING_VARS=()

for VAR in "${REQUIRED_ENV_VARS[@]}"; do
    if [ -z "${!VAR}" ]; then
        MISSING_VARS+=("$VAR")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}✗ 缺少以下环境变量:${NC}"
    for VAR in "${MISSING_VARS[@]}"; do
        echo "  - $VAR"
    done
    echo -e "请在.env文件中或运行前设置这些变量"
else
    echo -e "${GREEN}✓ 所有必要的环境变量已设置${NC}"
fi

# 检查目录结构
echo -e "\n${YELLOW}9. 检查目录结构${NC}"
REQUIRED_DIRS=("myfastapi" "Frontend" "docs")
MISSING_DIRS=()

for DIR in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$DIR" ]; then
        MISSING_DIRS+=("$DIR")
    fi
done

if [ ${#MISSING_DIRS[@]} -gt 0 ]; then
    echo -e "${RED}✗ 缺少以下目录:${NC}"
    for DIR in "${MISSING_DIRS[@]}"; do
        echo "  - $DIR"
    done
else
    echo -e "${GREEN}✓ 目录结构完整${NC}"
fi

# 显示系统总结
echo -e "\n${YELLOW}===== 系统检查摘要 =====${NC}"
echo -e "Python: ${PYTHON_VERSION}"
echo -e "Node.js: ${NODE_VERSION:-未安装}"
echo -e "PostgreSQL: ${PSQL_VERSION:-未安装或未在PATH中}"
echo -e "项目路径: ${PROJECT_ROOT}"

# 返回到原始目录
cd "$CURRENT_DIR" || exit 1

echo -e "\n${YELLOW}系统检查完成！${NC}"
