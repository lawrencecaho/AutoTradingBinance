# Python 环境相关问题与解决方案

## macOS Python 版本问题

### 问题描述
在 macOS 系统中存在多个 Python 版本：
1. 系统自带的 Python (`/usr/bin/python`)
2. Homebrew 安装的 Python3 (`/opt/homebrew/bin/python3`)
3. 虚拟环境中的 Python

这可能导致在执行 Python 脚本时使用了错误的 Python 版本。

### 具体问题
1. 即使在虚拟环境中，使用 `python` 命令可能仍指向系统 Python 版本
2. 需要明确使用 `python3` 来执行脚本
3. 在项目目录结构发生变化后（如移动文件到子目录），可能出现模块导入问题

### 解决方案
1. 使用虚拟环境的完整路径来执行 Python：
   ```bash
   ../venv/bin/python3 script.py
   ```

2. 或者先激活虚拟环境：
   ```bash
   source ../venv/bin/activate
   python3 script.py
   ```

## 模块导入问题

### 问题描述
当将 Python 文件移动到子目录（如从项目根目录移动到 `doapi/` 目录）后，可能出现无法导入父目录模块的问题。

### 解决方案
在需要导入父目录模块的 Python 文件中添加以下代码：
```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

这样就可以正常导入父目录中的模块了。

## 项目目录结构
```
AutoTradingBinance/
├── venv/                  # 虚拟环境
├── doapi/                 # API 相关代码
│   ├── __init__.py
│   ├── auth.py
│   ├── authtotp.py
│   ├── main.py
│   └── QRCodes/          # 存储生成的二维码
├── database.py           # 数据库相关代码
└── config.py            # 配置文件
```

## 最佳实践
1. 始终使用虚拟环境
2. 在 Python 脚本中使用相对导入
3. 使用 `python3` 而不是 `python`
4. 使用 `requirements.txt` 管理项目依赖
5. 确保项目结构清晰，避免循环导入

## 相关命令参考
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 导出依赖
pip freeze > requirements.txt

# 运行脚本（在 doapi 目录下）
../venv/bin/python3 authtotp.py --create --uid "user" --username "username"
```

## 环境检查命令
```bash
# 检查 Python 版本和路径
which python3
python3 --version
echo $VIRTUAL_ENV

# 检查已安装的包
pip list
```
