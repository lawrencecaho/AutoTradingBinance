#!/bin/bash
# security_check.sh
# 安全检查脚本，用于检查系统中的安全问题并提供修复建议

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
    print_green "✅ $1"
    return 0
  else
    print_red "❌ $1"
    return 1
  fi
}

# 打印分隔线
print_separator() {
  echo -e "\n${YELLOW}==============================================${NC}\n"
}

# 记录问题数量
ISSUES=0

# 当前目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || { print_red "无法切换到脚本目录"; exit 1; }

print_yellow "开始安全检查..."
print_separator

# 1. 检查密钥文件权限
print_yellow "1. 检查密钥文件权限"
KEY_DIRS=("myfastapi/Security" "Secret")

for dir in "${KEY_DIRS[@]}"; do
  if [ -d "$dir" ]; then
    # 检查目录权限 (macOS兼容)
    DIR_PERMS=$(stat -f "%Lp" "$dir" 2>/dev/null || stat -c "%a" "$dir" 2>/dev/null)
    if [ "$DIR_PERMS" != "700" ]; then
      print_red "❌ $dir 目录权限不安全，当前为 $DIR_PERMS，应为 700"
      print_yellow "  建议: chmod 700 $dir"
      ((ISSUES++))
    else
      print_green "✅ $dir 目录权限正确"
    fi
    
    # 检查目录内文件权限
    for file in "$dir"/*.pem "$dir"/*.key; do
      if [ -f "$file" ]; then
        FILE_PERMS=$(stat -f "%Lp" "$file" 2>/dev/null || stat -c "%a" "$file" 2>/dev/null)
        if [ "$FILE_PERMS" != "600" ]; then
          print_red "❌ $file 文件权限不安全，当前为 $FILE_PERMS，应为 600"
          print_yellow "  建议: chmod 600 $file"
          ((ISSUES++))
        else
          print_green "✅ $file 文件权限正确"
        fi
      fi
    done
  fi
done

print_separator

# 2. 检查环境变量配置
print_yellow "2. 检查环境变量配置"

# 读取.env文件（如果存在）
ENV_FILE=".env"
if [ -f "$ENV_FILE" ]; then
  # 检查权限 (macOS兼容)
  ENV_PERMS=$(stat -f "%Lp" "$ENV_FILE" 2>/dev/null || stat -c "%a" "$ENV_FILE" 2>/dev/null)
  if [ "$ENV_PERMS" != "600" ]; then
    print_red "❌ $ENV_FILE 文件权限不安全，当前为 $ENV_PERMS，应为 600"
    print_yellow "  建议: chmod 600 $ENV_FILE"
    ((ISSUES++))
  else
    print_green "✅ $ENV_FILE 文件权限正确"
  fi
  
  # 检查敏感环境变量（现在大部分由密钥管理系统处理）
  OPTIONAL_ENV_VARS=("DATABASE_URL" "REDIS_URL")
  
  for var in "${OPTIONAL_ENV_VARS[@]}"; do
    if ! grep -q "^$var=" "$ENV_FILE"; then
      print_yellow "⚠️ $ENV_FILE 中缺少 $var 变量（可选）"
    else
      print_green "✅ $ENV_FILE 包含 $var 变量"
    fi
  done
  
  # 检查已废弃的环境变量
  DEPRECATED_VARS=("JWT_SECRET" "API_SECRET_KEY")
  for var in "${DEPRECATED_VARS[@]}"; do
    if grep -q "^$var=" "$ENV_FILE"; then
      print_yellow "⚠️ 发现已废弃的环境变量 $var（现在由密钥管理系统自动处理）"
      print_yellow "  建议: 可以从 .env 文件中移除此变量"
    fi
  done
else
  print_yellow "⚠️ 未找到 .env 文件，跳过环境变量检查"
fi

print_separator

# 3. 检查密钥管理系统状态
print_yellow "3. 检查密钥管理系统状态"

# 使用Python脚本检查密钥管理系统
cat > check_key_management.py << 'EOF'
#!/usr/bin/env python3
"""检查密钥管理系统状态"""
import sys
import os

# 添加项目路径
sys.path.insert(0, '.')

try:
    # 检查密钥管理系统
    from myfastapi.security import get_all_secrets_info, get_api_secret, get_jwt_secret
    
    # 获取所有密钥信息
    info = get_all_secrets_info()
    
    print("密钥管理系统状态:")
    for key, value in info.items():
        if key == 'validity_days':
            print(f"  轮换周期: {value} 天")
        elif isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                if k == 'expired':
                    status = "❌ 已过期" if v else "✅ 有效"
                    print(f"    状态: {status}")
                elif k == 'age_days':
                    print(f"    使用天数: {v}")
                elif k == 'expires_in_days':
                    print(f"    剩余天数: {v}")
    
    # 检查密钥是否过期
    api_info = info.get('api_secret', {})
    jwt_info = info.get('jwt_secret', {})
    
    if api_info.get('expired', True) or jwt_info.get('expired', True):
        print("发现过期密钥")
        sys.exit(1)
    
    # 检查密钥是否接近过期（剩余时间 < 2天）
    api_remaining = api_info.get('expires_in_days', 0)
    jwt_remaining = jwt_info.get('expires_in_days', 0)
    
    if api_remaining < 2 or jwt_remaining < 2:
        print("密钥即将过期（剩余不足2天）")
        sys.exit(2)
    
    print("密钥管理系统运行正常")
    sys.exit(0)
    
except Exception as e:
    print(f"检查密钥管理系统失败: {str(e)}")
    sys.exit(1)
EOF

python3 check_key_management.py
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  print_green "✅ 密钥管理系统正常运行"
elif [ $EXIT_CODE -eq 1 ]; then
  print_red "❌ 发现过期密钥"
  print_yellow "  建议: 运行 python3 -c \"from myfastapi.security import force_regenerate_all_secrets; force_regenerate_all_secrets()\""
  ((ISSUES++))
elif [ $EXIT_CODE -eq 2 ]; then
  print_yellow "⚠️ 密钥即将过期"
  print_yellow "  建议: 考虑提前更新密钥"
else
  print_red "❌ 密钥管理系统检查失败"
  print_yellow "  建议: 检查 myfastapi/security.py 模块是否正常工作"
  ((ISSUES++))
fi

# 清理临时文件
rm -f check_key_management.py

print_separator

# 4. 检查敏感路由是否受保护
print_yellow "4. 检查敏感路由是否受保护"

# 搜索敏感API端点
API_FILES=("myfastapi/main.py" "myfastapi/auth.py")

for file in "${API_FILES[@]}"; do
  if [ -f "$file" ]; then
    print_yellow "检查 $file 中的API端点..."
    
    # 提取API端点
    ENDPOINTS=$(grep -E "@app\.(get|post|put|delete|patch)|@.*router\.(get|post|put|delete|patch)" "$file" | grep -v "verify_security_headers")
    
    # 检查每个端点是否包含安全验证
    echo "$ENDPOINTS" | while read -r line; do
      if [ -n "$line" ]; then
        ENDPOINT=$(echo "$line" | grep -oE '"/[^"]*"' | tr -d '"')
        if [ -n "$ENDPOINT" ]; then
          # 排除已废弃的端点（这些端点返回301重定向）
          if [[ "$ENDPOINT" =~ ^/(verify-otp|refresh-token)$ ]]; then
            print_yellow "⚠️ 端点 $ENDPOINT（已废弃，返回301重定向）"
            continue
          fi
          
          # 检查该端点是否包含安全验证
          NEXT_LINES=$(grep -A 15 "$line" "$file")
          if echo "$NEXT_LINES" | grep -q -E "Depends\(verify_security_headers\)|verify_token|authenticate|OAuth2PasswordBearer|get_current_user"; then
            print_green "✅ 端点 $ENDPOINT 已使用安全验证"
          else
            # 排除一些不需要验证的公共端点
            if [[ "$ENDPOINT" =~ ^/(security-info|register-client-key|api/hybrid-encrypt)$ ]]; then
              print_green "✅ 端点 $ENDPOINT（公共端点，无需验证）"
            else
              print_red "❌ 端点 $ENDPOINT 可能未受保护"
              print_yellow "  建议: 添加 Depends(verify_security_headers) 或类似安全措施"
              ((ISSUES++))
            fi
          fi
        fi
      fi
    done
  else
    print_yellow "⚠️ 文件 $file 不存在，跳过检查"
  fi
done

print_separator

# 5. 检查密码哈希和加密算法
print_yellow "5. 检查密码哈希和加密算法"

# 检查auth.py中是否使用了安全的哈希算法
if grep -q "CryptContext" "myfastapi/auth.py" 2>/dev/null; then
  if grep -q "bcrypt" "myfastapi/auth.py" 2>/dev/null; then
    print_green "✅ 使用了安全的密码哈希算法 (bcrypt)"
  else
    print_yellow "⚠️ 可能未使用最安全的哈希算法"
    print_yellow "  建议: 使用 bcrypt 作为首选哈希算法"
    ((ISSUES++))
  fi
else
  print_red "❌ 未检测到标准密码哈希机制"
  print_yellow "  建议: 使用 passlib.context.CryptContext 进行密码哈希"
  ((ISSUES++))
fi

# 检查加密算法
if grep -q "RSA-OAEP" "myfastapi/security.py" 2>/dev/null; then
  print_green "✅ 使用了安全的RSA-OAEP加密算法"
else
  print_yellow "⚠️ 未检测到使用RSA-OAEP加密算法"
  ((ISSUES++))
fi

if grep -q "key_size=2048" "myfastapi/security.py" 2>/dev/null; then
  print_green "✅ RSA密钥长度足够 (2048位)"
else
  print_yellow "⚠️ RSA密钥长度可能不足"
  print_yellow "  建议: 使用至少2048位的RSA密钥"
  ((ISSUES++))
fi

print_separator

# 6. 总结
print_yellow "安全检查完成"

if [ $ISSUES -eq 0 ]; then
  print_green "✅ 恭喜！未发现安全问题。"
else
  print_red "❌ 发现 $ISSUES 个潜在安全问题，请参考上述建议进行修复。"
fi

exit $ISSUES
