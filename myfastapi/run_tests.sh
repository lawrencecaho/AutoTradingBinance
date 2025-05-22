#!/bin/bash
# run_tests.sh
# 运行所有测试脚本，验证系统功能

# 设置终端颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_green() {
  echo -e "${GREEN}$1${NC}"
}

print_red() {
  echo -e "${RED}$1${NC}"
}

print_yellow() {
  echo -e "${YELLOW}$1${NC}"
}

# 检查上一个命令是否成功
check_status() {
  if [ $? -eq 0 ]; then
    print_green "✅ $1 测试通过"
    return 0
  else
    print_red "❌ $1 测试失败"
    return 1
  fi
}

# 打印分隔线
print_separator() {
  echo -e "\n${YELLOW}==============================================${NC}\n"
}

# 记录整体测试状态
OVERALL_STATUS=0

# 当前目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT" || { print_red "无法切换到项目根目录"; exit 1; }

print_yellow "开始测试 PostgreSQL 兼容的安全模块..."
print_separator

# 1. 测试数据库连接
print_yellow "1. 测试数据库连接和表操作"
python3 myfastapi/test_database_connection.py
check_status "数据库连接"
if [ $? -ne 0 ]; then
  OVERALL_STATUS=1
fi
print_separator

# 2. 测试安全模块
print_yellow "2. 测试安全模块功能"
python3 myfastapi/test_security.py
check_status "安全模块"
if [ $? -ne 0 ]; then
  OVERALL_STATUS=1
fi
print_separator

# 3. 检查API服务器是否运行
print_yellow "3. 检查API服务器状态"
if curl -s http://localhost:8000/security-info > /dev/null; then
  print_green "✅ API服务器正在运行"
  
  # 4. 集成测试
  print_yellow "4. 运行集成测试"
  python3 myfastapi/integration_test.py
  check_status "集成测试"
  if [ $? -ne 0 ]; then
    OVERALL_STATUS=1
  fi
  
  # 5. 响应加密测试
  print_yellow "5. 测试响应加密功能"
  python3 myfastapi/test_response_encryption.py
  check_status "响应加密测试"
  if [ $? -ne 0 ]; then
    OVERALL_STATUS=1
  fi
else
  print_red "❌ API服务器未运行，跳过集成测试"
  print_yellow "请在另一个终端中启动API服务器："
  print_yellow "cd $PROJECT_ROOT && uvicorn myfastapi.main:app --reload"
  OVERALL_STATUS=1
fi

print_separator
print_yellow "测试完成！"

# 总结测试结果
echo -e "\n${YELLOW}测试结果汇总：${NC}"
if [ $OVERALL_STATUS -eq 0 ]; then
  print_green "✅ 所有测试通过！系统工作正常。"
else
  print_red "❌ 部分测试失败，请查看上面的详细输出。"
fi
