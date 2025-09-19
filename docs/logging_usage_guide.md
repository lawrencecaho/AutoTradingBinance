# 项目日志配置使用指南

## 概述

本项目使用统一的日志配置系统，所有模块应该使用 `config/logging_config.py` 提供的配置，而不是各自独立配置日志。

## 快速开始

### 1. 在主入口文件中设置日志

```python
from config.logging_config import setup_logging

# 在应用启动时调用一次即可
setup_logging()
```

### 2. 在其他模块中使用日志

```python
from config.logging_config import get_logger

# 获取当前模块的日志记录器
logger = get_logger(__name__)

# 使用日志
logger.info("这是一条信息日志")
logger.error("这是一条错误日志")
logger.debug("这是一条调试日志")
```

## 环境变量配置

可以通过环境变量控制日志行为：

- `LOG_LEVEL`: 设置日志级别（DEBUG、INFO、WARNING、ERROR、CRITICAL）
- `ENVIRONMENT`: 设置环境（development/dev/local 为开发环境，其他为生产环境）

示例：
```bash
export LOG_LEVEL=DEBUG
export ENVIRONMENT=development
```

## 日志文件说明

项目会自动在 `logs/` 目录下创建以下日志文件：

- `app.log`: 应用主日志
- `error.log`: 错误日志
- `trading.log`: 交易相关日志
- `websocket.log`: WebSocket 数据日志
- `fastapi.log`: FastAPI 框架日志

所有日志文件都启用了轮转，最大 10MB，保留 5-10 个备份文件。

## 模块日志配置

不同模块有专门的日志配置：

- **ExchangeFetcher**: 输出到控制台、交易日志和 WebSocket 日志
- **DatabaseOperator**: 输出到控制台和应用日志
- **DataProcessingCalculator**: 输出到控制台和交易日志
- **WorkLine**: 输出到控制台和应用日志
- **myfastapi**: 输出到控制台和 FastAPI 日志

## 最佳实践

### ✅ 推荐做法

```python
# 正确：使用统一的日志配置
from config.logging_config import get_logger

logger = get_logger(__name__)
logger.info("操作成功")
```

### ❌ 避免做法

```python
# 错误：不要在各个模块中单独配置日志
import logging
logging.basicConfig(...)  # 不要这样做！

# 错误：不要直接使用 logging.getLogger()
logger = logging.getLogger(__name__)  # 不推荐
```

## 示例代码

### 完整的模块示例

```python
# my_module.py
from config.logging_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)

def my_function():
    try:
        logger.info("开始执行功能")
        # 你的业务逻辑
        result = some_operation()
        logger.info(f"功能执行成功，结果: {result}")
        return result
    except Exception as e:
        logger.error(f"功能执行失败: {e}", exc_info=True)
        raise

def some_operation():
    logger.debug("执行具体操作")
    return "success"
```

### 主应用示例

```python
# main.py
from config.logging_config import setup_logging, get_logger

def main():
    # 设置日志配置（整个应用只需调用一次）
    setup_logging()
    
    # 获取日志记录器
    logger = get_logger(__name__)
    
    logger.info("应用启动")
    
    try:
        # 你的应用逻辑
        pass
    except Exception as e:
        logger.error(f"应用执行错误: {e}", exc_info=True)
    finally:
        logger.info("应用结束")

if __name__ == "__main__":
    main()
```

## 故障排除

### 常见问题

1. **日志不显示**: 检查 `LOG_LEVEL` 环境变量设置
2. **日志文件不生成**: 确保有 `logs/` 目录的写入权限
3. **重复日志**: 确保只在主入口调用 `setup_logging()` 一次

### 调试技巧

```python
# 临时调整日志级别
import logging
logging.getLogger('your_module').setLevel(logging.DEBUG)

# 查看当前日志配置
import logging
print(logging.getLogger().handlers)
```

## 迁移现有代码

如果你有使用 `logging.basicConfig()` 的旧代码，请按以下步骤迁移：

1. 移除 `logging.basicConfig()` 调用
2. 移除自定义的日志配置函数
3. 导入并使用 `get_logger(__name__)`
4. 在主入口确保调用了 `setup_logging()`

这样就完成了日志配置的统一和优化！