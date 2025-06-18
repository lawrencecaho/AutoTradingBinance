# PathUniti 使用指南

## 概述

`PathUniti.py` 是一个统一的路径管理模块，用于管理整个项目中的所有路径配置。它解决了硬编码路径、路径配置分散等问题。

## 主要特性

1. **统一路径管理** - 所有路径配置都在一个地方
2. **自动Python路径设置** - 自动将项目目录添加到sys.path
3. **便捷函数** - 提供获取常用文件路径的便捷方法
4. **目录自动创建** - 自动创建必要的目录

## 可用的路径变量

### 基础路径
- `PROJECT_ROOT` - 项目根目录
- `APP_DIR` - app目录
- `DATA_DIR` - data目录 (自动创建)
- `LOGS_DIR` - logs目录 (自动创建)
- `DOCS_DIR` - docs目录
- `SECRET_DIR` - Secret目录

### App内部目录
- `DATABASE_DIR` - DatabaseOperator目录
- `FETCHER_DIR` - ExchangeFetcher目录
- `CALCULATOR_DIR` - DataProcessingCalculator目录
- `FASTAPI_DIR` - myfastapi目录
- `PROGRAM_MANAGER_DIR` - ProgramManager目录
- `EXCHANGE_BILL_DIR` - ExchangeBill目录

## 便捷函数

- `get_secret_file(filename)` - 获取Secret目录下的文件路径
- `get_config_file()` - 获取config.py文件路径
- `get_log_file(log_name)` - 获取日志文件路径

## 使用方法

### 方法1: 导入预定义变量

```python
from PathUniti import PROJECT_ROOT, APP_DIR, SECRET_DIR

# 直接使用
config_file = APP_DIR / "config.py"
api_key_file = SECRET_DIR / "api_secret.key"
```

### 方法2: 使用便捷函数

```python
from PathUniti import get_secret_file, get_log_file

# 获取Secret目录下的文件
private_key = get_secret_file("Binance-testnet-prvke.pem")
api_key = get_secret_file("api_secret.key")

# 获取日志文件
log_file = get_log_file("trading.log")
```

### 方法3: 使用路径管理器实例

```python
from PathUniti import path_manager

# 使用路径管理器的方法
database_path = path_manager.get_app_relative_path("DatabaseOperator/database.py")
custom_path = path_manager.get_relative_path("custom/directory")
```

## 项目文件修改示例

### 修改 config.py

```python
# 原来的写法
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
BINANCE_PRIVATE_KEY_PATH = PROJECT_ROOT / 'Secret' / 'Binance-testnet-prvke.pem'

# 使用PathUniti后
from PathUniti import get_secret_file
BINANCE_PRIVATE_KEY_PATH = get_secret_file('Binance-testnet-prvke.pem')
```

### 修改其他模块

```python
# 原来的写法
import sys
from pathlib import Path
_app_dir = Path(__file__).parent.parent
if str(_app_dir) not in sys.path:
    sys.path.insert(0, str(_app_dir))

# 使用PathUniti后
from PathUniti import APP_DIR  # Python路径已自动设置
```

## 自动化功能

导入 `PathUniti` 时会自动执行以下操作：

1. 设置Python路径 (将PROJECT_ROOT和APP_DIR添加到sys.path)
2. 创建必要的目录 (data, logs)
3. 初始化路径管理器实例

## 扩展PathUniti

如果需要添加新的路径配置，只需修改 `PathUniti.py` 中的 `PathManager` 类：

```python
def __init__(self):
    # 添加新的目录配置
    self.new_dir = self.project_root / "new_directory"
    
# 添加新的便捷函数
def get_new_file_path(self, filename: str) -> Path:
    return self.new_dir / filename

# 在文件末尾导出新的变量
NEW_DIR = path_manager.new_dir
get_new_file = path_manager.get_new_file_path
```

## 注意事项

1. **导入顺序**: PathUniti应该在其他项目模块之前导入
2. **路径检查**: 使用 `.exists()` 方法检查文件或目录是否存在
3. **相对路径**: 所有路径都基于项目根目录计算，确保可移植性

## 错误排查

如果遇到导入错误：

1. 确保 `PathUniti.py` 在正确的位置 (`app/PathUniti.py`)
2. 检查Python路径是否正确设置
3. 确认目标文件或目录是否存在

## 示例代码

参考 `app/path_usage_example.py` 获取完整的使用示例。
