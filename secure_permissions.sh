#!/bin/bash
# secure_permissions.sh
# 设置适当的文件权限，确保密钥安全

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

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
  print_yellow "注意: 未以root用户运行，可能无法修改某些文件权限"
fi

# 当前目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || { print_red "无法切换到脚本目录"; exit 1; }

print_yellow "开始设置安全文件权限..."

# 1. 设置密钥目录权限
KEY_DIRS=("myfastapi/Security" "Secret")

for dir in "${KEY_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    print_yellow "设置 $dir 目录权限为 700..."
    chmod 700 "$dir" && print_green "✅ 成功" || print_red "❌ 失败"
    
    # 设置密钥文件权限
    print_yellow "设置 $dir 目录下的密钥文件权限为 600..."
    find "$dir" -name "*.pem" -type f -exec chmod 600 {} \; && print_green "✅ 成功" || print_red "❌ 失败"
  else
    print_yellow "⚠️ 目录 $dir 不存在，跳过"
  fi
done

# 2. 设置.env文件权限
ENV_FILES=(".env" "Frontend/.env" "Frontend/.env.local" "Frontend/.env.production")

for file in "${ENV_FILES[@]}"; do
  if [ -f "$file" ]; then
    print_yellow "设置 $file 文件权限为 600..."
    chmod 600 "$file" && print_green "✅ 成功" || print_red "❌ 失败"
  else
    print_yellow "⚠️ 文件 $file 不存在，跳过"
  fi
done

# 3. 设置Python源代码文件权限
print_yellow "设置Python源代码文件权限为 644..."
find . -name "*.py" -type f -exec chmod 644 {} \; && print_green "✅ 成功" || print_red "❌ 失败"

# 4. 设置shell脚本文件权限
print_yellow "设置shell脚本文件权限为 755..."
find . -name "*.sh" -type f -exec chmod 755 {} \; && print_green "✅ 成功" || print_red "❌ 失败"

# 5. 设置日志文件权限
LOG_FILES=("fastapi.log")

for file in "${LOG_FILES[@]}"; do
  if [ -f "$file" ]; then
    print_yellow "设置 $file 日志文件权限为 640..."
    chmod 640 "$file" && print_green "✅ 成功" || print_red "❌ 失败"
  else
    print_yellow "⚠️ 文件 $file 不存在，跳过"
  fi
done

print_yellow "文件权限设置完成"

# 显示一些重要文件的权限
print_yellow "\n重要文件权限检查:"
ls -la myfastapi/Security 2>/dev/null || print_yellow "myfastapi/Security 目录不存在"
ls -la Secret 2>/dev/null || print_yellow "Secret 目录不存在"
ls -la .env 2>/dev/null || print_yellow ".env 文件不存在"

print_green "\n权限设置完成！系统现在更加安全。"
