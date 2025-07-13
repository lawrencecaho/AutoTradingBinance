# 平级别异步程序编写指南

## 目录
1. [异步编程基础概念](#异步编程基础概念)
2. [Python异步编程语法](#python异步编程语法)
3. [异步任务的组合方式](#异步任务的组合方式)
4. [实际应用场景](#实际应用场景)
5. [性能优化技巧](#性能优化技巧)
6. [常见错误和解决方案](#常见错误和解决方案)
7. [最佳实践](#最佳实践)

## 异步编程基础概念

### 什么是异步编程？
异步编程是一种编程范式，允许程序在等待某些操作（如网络请求、文件读写）完成时，不阻塞程序的执行，而是去执行其他任务。

### 同步 vs 异步对比

**同步代码示例：**
```python
import time
import requests

def fetch_prices_sync():
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    prices = {}
    
    start_time = time.time()
    for symbol in symbols:
        response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")
        prices[symbol] = response.json()["price"]
    
    print(f"同步获取耗时: {time.time() - start_time:.2f}秒")
    return prices
```

**异步代码示例：**
```python
import asyncio
import aiohttp
import time

async def fetch_prices_async():
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    
    async with aiohttp.ClientSession() as session:
        start_time = time.time()
        
        async def fetch_price(symbol):
            async with session.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}") as response:
                data = await response.json()
                return symbol, data["price"]
        
        # 并行执行所有请求
        tasks = [fetch_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        
        prices = dict(results)
        print(f"异步获取耗时: {time.time() - start_time:.2f}秒")
        return prices
```

## Python异步编程语法

### 核心关键字

1. **async def** - 定义异步函数
2. **await** - 等待异步操作完成
3. **asyncio** - 异步编程库

### 基本语法结构

```python
import asyncio

# 1. 定义异步函数
async def async_function():
    # 异步操作
    await asyncio.sleep(1)
    return "完成"

# 2. 调用异步函数
async def main():
    result = await async_function()
    print(result)

# 3. 运行异步程序
if __name__ == "__main__":
    asyncio.run(main())
```

### 异步上下文管理器

```python
class AsyncResource:
    async def __aenter__(self):
        print("获取资源")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("释放资源")

async def use_resource():
    async with AsyncResource() as resource:
        # 使用资源
        pass
```

## 异步任务的组合方式

### 1. 并行执行 (asyncio.gather)

```python
async def parallel_execution():
    # 所有任务同时开始，等待全部完成
    results = await asyncio.gather(
        fetch_data("A"),
        fetch_data("B"),
        fetch_data("C")
    )
    return results
```

### 2. 顺序执行

```python
async def sequential_execution():
    # 一个接一个执行
    result_a = await fetch_data("A")
    result_b = await fetch_data("B") 
    result_c = await fetch_data("C")
    return [result_a, result_b, result_c]
```

### 3. 条件执行

```python
async def conditional_execution():
    result_a = await fetch_data("A")
    
    if result_a.success:
        result_b = await fetch_data("B")
        return result_b
    else:
        return await handle_error()
```

### 4. 限制并发数量

```python
async def limited_concurrency():
    semaphore = asyncio.Semaphore(3)  # 最多3个并发
    
    async def fetch_with_limit(item):
        async with semaphore:
            return await fetch_data(item)
    
    tasks = [fetch_with_limit(item) for item in range(10)]
    results = await asyncio.gather(*tasks)
    return results
```

### 5. 任务超时控制

```python
async def timeout_control():
    try:
        result = await asyncio.wait_for(
            slow_operation(), 
            timeout=5.0
        )
        return result
    except asyncio.TimeoutError:
        print("操作超时")
        return None
```

### 6. 等待第一个完成

```python
async def wait_for_first():
    tasks = [
        fetch_from_source1(),
        fetch_from_source2(),
        fetch_from_source3()
    ]
    
    done, pending = await asyncio.wait(
        tasks, 
        return_when=asyncio.FIRST_COMPLETED
    )
    
    # 取消未完成的任务
    for task in pending:
        task.cancel()
    
    return done.pop().result()
```

## 实际应用场景

### 1. 网络请求密集型应用

```python
class AsyncAPIClient:
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def fetch_multiple_endpoints(self, urls):
        tasks = [self.session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        
        results = []
        for response in responses:
            data = await response.json()
            results.append(data)
        
        return results
```

### 2. 数据库操作优化

```python
# 需要安装: pip install asyncpg
import asyncpg

class AsyncDatabase:
    def __init__(self, database_url):
        self.database_url = database_url
        self.pool = None
    
    async def connect(self):
        self.pool = await asyncpg.create_pool(self.database_url)
    
    async def execute_batch(self, queries):
        async with self.pool.acquire() as connection:
            # 并行执行多个查询
            tasks = [connection.execute(query) for query in queries]
            results = await asyncio.gather(*tasks)
            return results
    
    async def close(self):
        await self.pool.close()
```

### 3. 文件I/O操作

```python
# 需要安装: pip install aiofiles
import aiofiles

async def process_multiple_files(file_paths):
    async def read_file(path):
        async with aiofiles.open(path, 'r') as file:
            content = await file.read()
            return len(content)
    
    tasks = [read_file(path) for path in file_paths]
    file_sizes = await asyncio.gather(*tasks)
    return file_sizes
```

### 4. 实时数据处理

```python
class AsyncDataProcessor:
    def __init__(self):
        self.data_queue = asyncio.Queue()
        self.processing = False
    
    async def start_processing(self):
        self.processing = True
        
        # 并行运行数据收集和处理
        await asyncio.gather(
            self.data_collector(),
            self.data_processor()
        )
    
    async def data_collector(self):
        while self.processing:
            # 模拟数据收集
            data = await self.fetch_real_time_data()
            await self.data_queue.put(data)
            await asyncio.sleep(0.1)
    
    async def data_processor(self):
        while self.processing:
            try:
                data = await asyncio.wait_for(
                    self.data_queue.get(), 
                    timeout=1.0
                )
                await self.process_data(data)
            except asyncio.TimeoutError:
                continue
```

## 性能优化技巧

### 1. 连接池管理

```python
class OptimizedClient:
    def __init__(self):
        # 配置连接池
        connector = aiohttp.TCPConnector(
            limit=100,  # 总连接数限制
            limit_per_host=30,  # 每个主机连接数限制
            ttl_dns_cache=300,  # DNS缓存时间
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,  # 总超时时间
            connect=10,  # 连接超时时间
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
```

### 2. 批量操作优化

```python
async def batch_process(items, batch_size=10):
    """分批处理大量数据"""
    results = []
    
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_tasks = [process_item(item) for item in batch]
        batch_results = await asyncio.gather(*batch_tasks)
        results.extend(batch_results)
        
        # 批次间短暂等待，避免过载
        await asyncio.sleep(0.1)
    
    return results
```

### 3. 内存管理

```python
async def memory_efficient_processing(large_dataset):
    """内存高效的数据处理"""
    semaphore = asyncio.Semaphore(5)  # 限制并发数
    
    async def process_chunk(chunk):
        async with semaphore:
            result = await expensive_operation(chunk)
            # 及时释放内存
            del chunk
            return result
    
    # 分块处理
    chunk_size = 1000
    tasks = []
    
    for i in range(0, len(large_dataset), chunk_size):
        chunk = large_dataset[i:i + chunk_size]
        task = asyncio.create_task(process_chunk(chunk))
        tasks.append(task)
        
        # 控制内存使用
        if len(tasks) >= 10:
            results = await asyncio.gather(*tasks)
            tasks.clear()
            yield results
    
    # 处理剩余任务
    if tasks:
        results = await asyncio.gather(*tasks)
        yield results
```

## 常见错误和解决方案

### 1. 忘记使用await

```python
# 错误❌
async def wrong_way():
    result = async_function()  # 这返回的是协程对象，不是结果
    return result

# 正确✅
async def correct_way():
    result = await async_function()  # 等待协程完成
    return result
```

### 2. 在同步函数中调用异步函数

```python
# 错误❌
def sync_function():
    result = await async_function()  # SyntaxError

# 正确✅
def sync_function():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(async_function())
    return result

# 更好的方式✅
async def async_wrapper():
    return await async_function()

def sync_function():
    return asyncio.run(async_wrapper())
```

### 3. 未正确处理异常

```python
# 错误❌ - 异常可能会静默失败
async def risky_operations():
    tasks = [risky_operation(i) for i in range(10)]
    results = await asyncio.gather(*tasks)  # 一个失败，全部失败

# 正确✅ - 单独处理每个任务的异常
async def safe_operations():
    tasks = [risky_operation(i) for i in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_results = []
    for result in results:
        if isinstance(result, Exception):
            print(f"任务失败: {result}")
        else:
            success_results.append(result)
    
    return success_results
```

### 4. 资源泄漏

```python
# 错误❌ - 可能导致资源泄漏
async def resource_leak():
    session = aiohttp.ClientSession()
    response = await session.get("http://example.com")
    return await response.text()
    # session没有被关闭

# 正确✅ - 使用上下文管理器
async def proper_resource_management():
    async with aiohttp.ClientSession() as session:
        async with session.get("http://example.com") as response:
            return await response.text()
    # 资源自动清理
```

## 最佳实践

### 1. 异步函数设计原则

```python
# 好的异步函数设计
async def well_designed_async_function(
    data: List[str], 
    timeout: float = 10.0,
    max_concurrency: int = 5
) -> List[Dict]:
    """
    设计良好的异步函数应该：
    1. 有清晰的类型注释
    2. 提供合理的默认值
    3. 包含错误处理
    4. 支持并发控制
    """
    semaphore = asyncio.Semaphore(max_concurrency)
    
    async def process_item(item: str) -> Dict:
        async with semaphore:
            try:
                return await asyncio.wait_for(
                    expensive_operation(item),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                return {"item": item, "error": "timeout"}
            except Exception as e:
                return {"item": item, "error": str(e)}
    
    tasks = [process_item(item) for item in data]
    results = await asyncio.gather(*tasks)
    return results
```

### 2. 日志和监控

```python
import logging
import time

logger = logging.getLogger(__name__)

def async_timer(func):
    """异步函数性能监控装饰器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} 执行成功，耗时: {duration:.2f}秒")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败，耗时: {duration:.2f}秒，错误: {e}")
            raise
    return wrapper

@async_timer
async def monitored_function():
    await asyncio.sleep(1)
    return "完成"
```

### 3. 配置管理

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class AsyncConfig:
    """异步操作配置"""
    max_concurrency: int = 10
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    connection_pool_size: int = 100

class ConfigurableAsyncClient:
    def __init__(self, config: AsyncConfig):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def setup(self):
        connector = aiohttp.TCPConnector(
            limit=self.config.connection_pool_size
        )
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout
        )
    
    async def fetch_with_retry(self, url: str):
        for attempt in range(self.config.retry_attempts):
            try:
                async with self.session.get(url) as response:
                    return await response.json()
            except Exception as e:
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                raise e
```

### 4. 测试异步代码

```python
import pytest

class TestAsyncFunctions:
    @pytest.mark.asyncio
    async def test_async_function(self):
        """异步函数测试"""
        result = await async_function("test_input")
        assert result == "expected_output"
    
    @pytest.mark.asyncio
    async def test_async_function_with_mock(self, mocker):
        """使用mock测试异步函数"""
        mock_fetch = mocker.patch('module.fetch_data')
        mock_fetch.return_value = asyncio.Future()
        mock_fetch.return_value.set_result("mocked_data")
        
        result = await function_that_uses_fetch()
        assert result == "processed_mocked_data"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """测试并发操作"""
        tasks = [async_operation(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
```

## 总结

异步编程的核心优势：

1. **提高性能** - 在I/O密集型应用中显著提升性能
2. **资源利用** - 更好地利用系统资源
3. **响应性** - 提高应用程序的响应性
4. **扩展性** - 支持更高的并发量

关键要点：

- 理解何时使用异步（I/O密集型 vs CPU密集型）
- 正确使用 `async`/`await` 语法
- 合理组合异步任务
- 妥善处理异常和资源管理
- 进行性能监控和优化

通过遵循这些最佳实践，您可以编写出高效、可靠的异步程序。
