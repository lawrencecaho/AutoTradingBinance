# 日志配置迁移指南

## 🔍 **现有问题分析**

你的项目目前存在以下日志配置问题：

1. **多套不一致的日志配置**
   - `logging.conf` - 传统配置文件格式
   - FastAPI 中的 `LOGGING_CONFIG` - 字典格式
   - 各模块中的独立 `logging.basicConfig()`

2. **日志文件分散**
   - 不同模块写入不同的日志文件
   - 缺乏统一的日志轮转和管理

3. **配置冲突**
   - 多个模块都试图配置日志系统
   - 可能导致日志配置被覆盖

## ✅ **新的统一日志配置**

### **主要特性**
- 🔧 **统一配置**: 一套配置管理所有模块
- 📁 **分类日志**: 不同类型的日志写入不同文件
- 🔄 **自动轮转**: 防止日志文件过大
- 🎨 **格式统一**: 所有日志使用一致的格式
- 🚀 **简单易用**: 一行代码即可使用

### **日志文件分类**
```
logs/
├── app.log           # 主应用日志
├── error.log         # 错误日志
├── trading.log       # 交易相关日志
├── websocket.log     # WebSocket日志
└── fastapi.log       # FastAPI服务日志
```

## 🔄 **迁移步骤**

### **1. 简单模块迁移**

**旧代码：**
```python
import logging
logging.basicConfig(...)
logger = logging.getLogger(__name__)
```

**新代码：**
```python
from config import get_logger
logger = get_logger()  # 自动获取模块名
```

### **2. FastAPI 应用迁移**

**旧代码 (main.py)：**
```python
LOGGING_CONFIG = { ... }
# 复杂的配置字典
```

**新代码：**
```python
from config import PROJECT_LOGGING_CONFIG
# 在 uvicorn.run() 中使用
uvicorn.run(app, log_config=PROJECT_LOGGING_CONFIG)
```

### **3. 专用日志记录器**

```python
from config import get_trading_logger, get_websocket_logger

trading_logger = get_trading_logger()
websocket_logger = get_websocket_logger()

trading_logger.info("交易事件")
websocket_logger.debug("连接状态")
```

## 📋 **具体文件迁移建议**

### **1. ExchangeFetcher/fetcher.py**
```python
# 在文件开头添加
from config import get_logger
logger = get_logger(__name__)

# 或者使用专用日志记录器
from config import get_websocket_logger
websocket_logger = get_websocket_logger()
```

### **2. DatabaseOperator/*.py**
```python
from config import get_logger
logger = get_logger(__name__)
```

### **3. myfastapi/main.py**
```python
from config import PROJECT_LOGGING_CONFIG

# 替换现有的 LOGGING_CONFIG
# 在 uvicorn.run() 中使用新配置
uvicorn.run(
    app,
    host="127.0.0.1",
    port=8765,
    log_config=PROJECT_LOGGING_CONFIG,
    # ... 其他参数
)
```

### **4. 废弃文件**
可以删除或重命名：
- `logging.conf` → `logging.conf.old`

## 🚀 **立即开始使用**

### **最简单的方式**
在任何脚本开头添加：
```python
from config import quick_setup, get_logger

quick_setup()  # 一行配置全部日志
logger = get_logger()  # 获取日志记录器

logger.info("开始使用统一日志配置！")
```

### **测试新配置**
```bash
cd app
uv run python3 -m examples.logging_usage_example
```

## 💡 **最佳实践**

1. **模块级别使用**
   ```python
   from config import get_logger
   logger = get_logger(__name__)
   ```

2. **业务逻辑分类**
   ```python
   from config import get_trading_logger, get_websocket_logger
   ```

3. **初始化脚本**
   ```python
   from config import quick_setup
   quick_setup()  # 在主脚本开头调用
   ```

4. **错误处理**
   ```python
   try:
       # 业务代码
   except Exception as e:
       logger.error(f"操作失败: {e}", exc_info=True)
   ```

## 🔍 **验证迁移成功**

迁移后检查：
1. `logs/` 目录下的日志文件是否正常生成
2. 控制台输出是否格式统一
3. 不同模块的日志是否正确分类
4. 日志轮转是否正常工作

## 📞 **需要帮助？**

如果在迁移过程中遇到问题，可以：
1. 运行测试示例检查配置
2. 检查 `logs/error.log` 查看错误信息
3. 使用 `get_logger()` 替代所有旧的日志配置