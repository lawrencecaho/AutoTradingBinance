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
    
    # 设置所有类型的密钥文件权限
    print_yellow "设置 $dir 目录下的密钥文件权限为 600..."
    
    # 处理各种密钥文件类型
    KEY_EXTENSIONS=("*.pem" "*.key" "*.crt" "*.p12" "*.pfx")
    KEY_FILES_FOUND=false
    
    for ext in "${KEY_EXTENSIONS[@]}"; do
      # 使用更安全的方式检查文件存在
      if find "$dir" -maxdepth 1 -name "$ext" -type f | grep -q .; then
        find "$dir" -maxdepth 1 -name "$ext" -type f -exec chmod 600 {} \;
        print_green "✅ 已处理 $ext 类型文件"
        KEY_FILES_FOUND=true
      fi
    done
    
    if [ "$KEY_FILES_FOUND" = true ]; then
      print_green "✅ 密钥文件权限设置成功"
    else
      print_yellow "⚠️ 在 $dir 中未找到密钥文件"
    fi
    
    # 显示目录内容（用于验证）
    print_yellow "检查 $dir 目录内容："
    ls -la "$dir" 2>/dev/null | head -10
    
  else
    print_yellow "⚠️ 目录 $dir 不存在，跳过"
  fi
done

# 2. 设置.env文件权限
ENV_FILES=(".env" ".env.local" ".env.production" ".env.example")

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
LOG_FILES=("fastapi.log" "myfastapi/fastapi.log")

for file in "${LOG_FILES[@]}"; do
  if [ -f "$file" ]; then
    print_yellow "设置 $file 日志文件权限为 640..."
    chmod 640 "$file" && print_green "✅ 成功" || print_red "❌ 失败"
  else
    print_yellow "⚠️ 文件 $file 不存在，跳过"
  fi
done

# 6. 设置特殊配置文件权限
print_yellow "设置特殊配置文件权限..."
CONFIG_FILES=("config.py" "requirements.txt" "setup.py")

for file in "${CONFIG_FILES[@]}"; do
  if [ -f "$file" ]; then
    chmod 644 "$file" && print_green "✅ $file 权限设置为 644" || print_red "❌ $file 权限设置失败"
  fi
done

# 7. 验证密钥管理系统文件权限
print_yellow "验证密钥管理系统相关文件..."
SECURITY_FILES=("myfastapi/security.py" "myfastapi/auth.py" "myfastapi/authtotp.py")

for file in "${SECURITY_FILES[@]}"; do
  if [ -f "$file" ]; then
    chmod 644 "$file" && print_green "✅ $file 权限设置为 644" || print_red "❌ $file 权限设置失败"
  fi
done

print_yellow "文件权限设置完成"

# 显示重要文件的权限状态
print_yellow "\n📋 重要文件权限检查:"

# 检查密钥目录
for dir in "${KEY_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    print_yellow "\n🔐 $dir 目录:"
    
    # macOS 和 Linux 兼容的权限检查
    DIR_PERMS=$(stat -f "%Lp" "$dir" 2>/dev/null || stat -c "%a" "$dir" 2>/dev/null)
    if [ "$DIR_PERMS" = "700" ]; then
      print_green "✅ 目录权限正确: $DIR_PERMS"
    else
      print_red "❌ 目录权限不正确: $DIR_PERMS (应为 700)"
    fi
    
    # 检查目录内的密钥文件
    find "$dir" -type f \( -name "*.pem" -o -name "*.key" -o -name "*.crt" \) 2>/dev/null | while read -r file; do
      if [ -f "$file" ]; then
        FILE_PERMS=$(stat -f "%Lp" "$file" 2>/dev/null || stat -c "%a" "$file" 2>/dev/null)
        if [ "$FILE_PERMS" = "600" ]; then
          print_green "✅ $(basename "$file"): $FILE_PERMS"
        else
          print_red "❌ $(basename "$file"): $FILE_PERMS (应为 600)"
        fi
      fi
    done
  else
    print_yellow "⚠️ 目录 $dir 不存在"
  fi
done

# 检查环境文件
print_yellow "\n🌍 环境配置文件:"
for file in ".env" ".env.local" ".env.production"; do
  if [ -f "$file" ]; then
    ls -la "$file"
  fi
done

# 检查关键安全文件
print_yellow "\n🛡️ 安全相关文件:"
for file in "myfastapi/security.py" "myfastapi/auth.py"; do
  if [ -f "$file" ]; then
    ls -la "$file"
  fi
done

# 提供权限修复建议
print_yellow "\n💡 权限设置建议:"
print_green "✅ 密钥文件和目录: 600/700 (仅所有者访问)"
print_green "✅ 环境配置文件: 600 (仅所有者读写)"
print_green "✅ Python 源代码: 644 (所有者读写，其他人只读)"
print_green "✅ Shell 脚本: 755 (所有者执行，其他人读取执行)"
print_green "✅ 日志文件: 640 (所有者读写，组成员只读)"

print_green "\n🎉 权限设置完成！系统现在更加安全。"

# 可选：运行安全检查
if [ -f "security_check.sh" ]; then
  print_yellow "\n🔍 是否要运行安全检查？ (y/N)"
  read -r response
  if [[ "$response" =~ ^[Yy]$ ]]; then
    print_yellow "运行安全检查..."
    bash security_check.sh
  fi
fi
