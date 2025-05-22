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
    # 检查目录权限
    if [ "$(stat -c %a $dir)" != "700" ]; then
      print_red "❌ $dir 目录权限不安全，应为 700"
      print_yellow "  建议: chmod 700 $dir"
      ((ISSUES++))
    else
      print_green "✅ $dir 目录权限正确"
    fi
    
    # 检查目录内文件权限
    for file in "$dir"/*.pem; do
      if [ -f "$file" ]; then
        if [ "$(stat -c %a $file)" != "600" ]; then
          print_red "❌ $file 文件权限不安全，应为 600"
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
  # 检查权限
  if [ "$(stat -c %a $ENV_FILE)" != "600" ]; then
    print_red "❌ $ENV_FILE 文件权限不安全，应为 600"
    print_yellow "  建议: chmod 600 $ENV_FILE"
    ((ISSUES++))
  else
    print_green "✅ $ENV_FILE 文件权限正确"
  fi
  
  # 检查敏感环境变量
  REQUIRED_ENV_VARS=("JWT_SECRET" "API_SECRET_KEY" "DATABASE_URL")
  
  for var in "${REQUIRED_ENV_VARS[@]}"; do
    if ! grep -q "^$var=" "$ENV_FILE"; then
      print_red "❌ $ENV_FILE 中缺少 $var 变量"
      ((ISSUES++))
    else
      print_green "✅ $ENV_FILE 包含 $var 变量"
    fi
  done
else
  print_yellow "⚠️ 未找到 .env 文件，跳过环境变量检查"
fi

print_separator

# 3. 检查密钥是否过期
print_yellow "3. 检查密钥是否过期"

# 使用Python脚本检查密钥状态
cat > check_keys.py << 'EOF'
#!/usr/bin/env python3
"""检查密钥状态"""
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from sqlalchemy import create_engine, select
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import Table, MetaData
except ImportError:
    logger.error("未安装所需库，请使用 pip install sqlalchemy 安装")
    sys.exit(1)

# 尝试从环境变量或配置文件获取数据库URL
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    try:
        from config import DATABASE_URL
        database_url = DATABASE_URL
    except (ImportError, AttributeError):
        logger.error("未找到数据库URL")
        sys.exit(1)

# 创建引擎和会话
try:
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    metadata = MetaData()
    
    # 反射数据库结构
    metadata.reflect(bind=engine)
    
    # 检查global_options表是否存在
    if 'global_options' in metadata.tables:
        global_options = metadata.tables['global_options']
        
        # 获取密钥信息
        with Session() as session:
            # 检查私钥
            query = select(global_options).where(global_options.c.varb == "private_key")
            private_key_row = session.execute(query).fetchone()
            
            if private_key_row and hasattr(private_key_row, 'fixed_time'):
                fixed_time = private_key_row.fixed_time
                current_time = datetime.now()
                days_old = (current_time - fixed_time).days
                
                if days_old > 30:
                    print(f"私钥已过期，已使用 {days_old} 天（超过30天）")
                    sys.exit(1)
                else:
                    print(f"私钥有效，已使用 {days_old} 天")
                    sys.exit(0)
            else:
                print("未找到私钥信息")
                sys.exit(1)
    else:
        print("global_options表不存在")
        sys.exit(1)
except Exception as e:
    print(f"检查密钥失败: {str(e)}")
    sys.exit(1)
EOF

python3 check_keys.py
if [ $? -eq 0 ]; then
  print_green "✅ 密钥有效"
else
  print_red "❌ 密钥已过期或检查失败"
  print_yellow "  建议: 使用 security.py 中的 load_or_generate_rsa_keys(force_generate=True) 生成新密钥"
  ((ISSUES++))
fi

# 清理临时文件
rm -f check_keys.py

print_separator

# 4. 检查敏感路由是否受保护
print_yellow "4. 检查敏感路由是否受保护"

# 搜索敏感API端点
API_FILES=("myfastapi/main.py" "myfastapi/auth.py" "doapi/main.py")

for file in "${API_FILES[@]}"; do
  if [ -f "$file" ]; then
    print_yellow "检查 $file 中的API端点..."
    
    # 提取API端点
    ENDPOINTS=$(grep -E "@app\.(get|post|put|delete|patch)" "$file" | grep -v "verify_security_headers")
    
    # 检查每个端点是否包含安全验证
    echo "$ENDPOINTS" | while read -r line; do
      ENDPOINT=$(echo "$line" | grep -oE '"/[^"]*"' | tr -d '"')
      if [ -n "$ENDPOINT" ]; then
        # 检查该端点是否包含安全验证
        NEXT_LINES=$(grep -A 10 "$line" "$file")
        if echo "$NEXT_LINES" | grep -q -E "Depends\(verify_security_headers\)|verify_token|authenticate|OAuth2PasswordBearer"; then
          print_green "✅ 端点 $ENDPOINT 已使用安全验证"
        else
          print_red "❌ 端点 $ENDPOINT 可能未受保护"
          print_yellow "  建议: 添加 Depends(verify_security_headers) 或类似安全措施"
          ((ISSUES++))
        fi
      fi
    done
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
