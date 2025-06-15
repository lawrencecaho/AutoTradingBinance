#!/bin/bash
# update_deps.sh - 更新项目依赖和检查新版本

echo "正在更新项目依赖..."

# 保存当前目录
CURRENT_DIR=$(pwd)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 确保在项目根目录中
cd "$PROJECT_ROOT" || exit 1

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
  source venv/bin/activate
  echo "已激活虚拟环境"
fi

# 更新Python依赖
echo "===== 更新Python依赖 ====="
pip list --outdated

# 备份当前requirements.txt
pip freeze > requirements.txt.old

# 获取过期包列表并更新
echo "正在更新过期的包..."
pip list --outdated --format=columns | tail -n +3 | awk '{print $1}' | xargs -n1 pip install -U

# 生成新的requirements.txt，排除自引用
echo "生成新的requirements.txt（排除项目自引用）..."
pip freeze | grep -v -E "(autotradingbinance|AutoTradingBinance)" | grep -v "^-e git+" > requirements.txt

echo "Python依赖已更新，旧版本信息保存在 requirements.txt.old"


# 检查系统配置
echo "===== 检查系统配置 ====="

# 检查数据库连接配置
if [ -f "config.py" ]; then
  if grep -q "DATABASE_URL" "config.py"; then
    echo "✅ 数据库配置文件存在"
  else
    echo "⚠️  警告: config.py 中未找到 DATABASE_URL 配置"
  fi
else
  echo "❌ 错误: config.py 配置文件不存在"
fi

# 检查密钥管理系统
if [ -f "myfastapi/security.py" ]; then
  echo "✅ 密钥管理系统文件存在"
  
  # 测试密钥管理系统功能
  if python3 -c "
import sys
import os
sys.path.insert(0, '.')
try:
    from myfastapi.security import get_api_secret, get_jwt_secret
    api_secret = get_api_secret()
    jwt_secret = get_jwt_secret()
    if api_secret and jwt_secret:
        print('✅ 密钥管理系统工作正常')
        print(f'API Secret 长度: {len(api_secret)}')
        print(f'JWT Secret 长度: {len(jwt_secret)}')
        exit(0)
    else:
        print('❌ 密钥获取失败')
        exit(1)
except Exception as e:
    print(f'❌ 密钥管理系统测试失败: {e}')
    exit(1)
  " 2>/dev/null; then
    echo "✅ 密钥管理系统测试通过"
  else
    echo "⚠️  警告: 密钥管理系统测试失败，请检查配置"
  fi
else
  echo "❌ 错误: myfastapi/security.py 密钥管理文件不存在"
fi

# 检查可选的环境变量
echo ""
echo "检查可选的环境变量配置:"
OPTIONAL_ENV_VARS=("DATABASE_URL" "REDIS_URL")
for VAR in "${OPTIONAL_ENV_VARS[@]}"; do
  if [ -n "${!VAR}" ]; then
    echo "  ✅ $VAR: 已设置"
  else
    echo "  ⚪ $VAR: 未设置（可从配置文件获取）"
  fi
done

# 返回到原始目录
cd "$CURRENT_DIR" || exit 1

echo ""
echo "🎉 依赖更新完成！"
echo ""
echo "📋 更新摘要:"
echo "  - Python包已更新到最新版本"
echo "  - requirements.txt 已刷新（排除项目自引用）"
echo "  - 系统配置检查完成"
echo ""
echo "🚀 下一步操作:"
echo "  - 启动应用: python3 myfastapi/main.py"
echo "  - 运行测试: bash myfastapi/run_tests.sh"
echo "  - 检查系统: bash check_system.sh"
echo ""
