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
pip freeze > requirements.txt.old
pip list --outdated --format=freeze | cut -d = -f 1 | xargs -n1 pip install -U
pip freeze > requirements.txt

echo "Python依赖已更新，旧版本信息保存在 requirements.txt.old"


# 检查环境变量
echo "===== 检查环境变量 ====="
REQUIRED_ENV_VARS=("DATABASE_URL" "JWT_SECRET" "API_SECRET_KEY")
MISSING_VARS=()

# 检查环境变量
for VAR in "${REQUIRED_ENV_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    MISSING_VARS+=("$VAR")
  fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
  echo "警告: 以下必要的环境变量未设置:"
  for VAR in "${MISSING_VARS[@]}"; do
    echo "  - $VAR"
  done
  echo "请确保在运行应用前设置这些变量"
else
  echo "所有必要的环境变量已设置"
fi

# 返回到原始目录
cd "$CURRENT_DIR" || exit 1

echo "依赖更新完成！"
