# 队列管理API文档

## 📊 概述

 `ExchangeDataFetcherQueueSettings` 便捷名称 `EDFQS` 使用 PostgreSQL，并创建了完整的REST API接口用于队列配置管理。

## 🗃️ 数据库设计

### 表结构：`fetcher_queue_configs`

```sql
CREATE TABLE fetcher_queue_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    queue_name VARCHAR(255) UNIQUE NOT NULL,
    symbol VARCHAR(50) NOT NULL,
    exchange VARCHAR(50) NOT NULL DEFAULT 'binance',
    interval VARCHAR(10) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 字段说明
- `id`: UUID主键，自动生成
- `queue_name`: 队列名称，唯一标识符
- `symbol`: 交易对符号（如 BTCUSDT）
- `exchange`: 交易所名称（目前只支持 binance）
- `interval`: K线周期（1m, 5m, 1h, 1d等）
- `is_active`: 队列激活状态（Boolean类型），默认为 false（不激活）
- `description`: 队列描述信息
- `created_at` / `updated_at`: 时间戳字段

## 🔌 API 端点

### 基础信息
- **基础路径**: `/api/queue/edfqs` (EDFQS = Exchange Data Fetcher Queue Settings)
- **认证**: 需要安全头部验证
- **加密**: 所有请求和响应都使用混合加密

### 端点列表

#### 1. 获取所有队列配置
```
GET /api/queue/edfqs/list?active_only=true
```
- **查询参数**:
  - `active_only` (boolean): 是否只返回激活的队列，默认 true
- **响应**: 加密的队列配置列表

#### 2. 获取特定队列配置
```
GET /api/queue/edfqs/{queue_name}
```
- **路径参数**:
  - `queue_name`: 队列名称
- **响应**: 加密的队列配置信息

#### 3. 创建新队列配置
```
POST /api/queue/edfqs/create
```
- **请求体**: 加密的队列配置数据
- **字段**:
  - `queue_name` (必填): 队列名称
  - `symbol` (必填): 交易对符号
  - `interval` (必填): K线周期
  - `exchange` (可选): 交易所名称，默认 "binance"
  - `description` (可选): 描述信息
- **安全规则**: 创建的队列默认为不激活状态，前端无法在创建时指定激活状态

#### 4. 更新队列配置
```
PUT /api/queue/edfqs/{queue_name}
```
- **业务规则**:
  - 激活状态的队列只能修改 `queue_name` 和 `description`
  - 非激活状态的队列可以修改除ID外的所有字段

#### 5. 激活队列
```
POST /api/queue/edfqs/{queue_name}/activate
```

#### 6. 停用队列
```
POST /api/queue/edfqs/{queue_name}/deactivate
```

#### 7. 删除队列配置
```
DELETE /api/queue/edfqs/{queue_name}/delete
```
- **业务规则**: 激活状态的队列不能删除

### 向后兼容端点

为了向后兼容，系统还提供了简化路径的端点：

#### 3. 创建新队列配置
```
POST /api/queue/create
```
- **请求体**: 加密的队列配置数据
- **字段**:
  - `queue_name` (必填): 队列名称
  - `symbol` (必填): 交易对符号
  - `interval` (必填): K线周期
  - `exchange` (可选): 交易所名称，默认 "binance"
  - `description` (可选): 描述信息
- **安全规则**: 创建的队列默认为不激活状态，前端无法在创建时指定激活状态

#### 4. 更新队列配置
```
PUT /api/queue/{queue_name}
```
- **业务规则**:
  - 激活状态的队列只能修改 `queue_name` 和 `description`
  - 非激活状态的队列可以修改除ID外的所有字段

#### 5. 激活队列
```
POST /api/queue/{queue_name}/activate
```

#### 6. 停用队列
```
POST /api/queue/{queue_name}/deactivate
```

#### 7. 删除队列配置
```
DELETE /api/queue/{queue_name}
```
- **业务规则**: 激活状态的队列不能删除

## 💾 数据管理

### Python接口
```python
from DatabaseOperator.pg_operator import fetcher_queue_manager

# 创建队列配置
result = fetcher_queue_manager.create_queue_config(
    queue_name="btc_1m_queue",
    symbol="BTCUSDT", 
    interval="1m",
    exchange="binance",
    description="BTC 1分钟K线数据获取队列"
)

# 获取队列配置
config = fetcher_queue_manager.get_queue_config("btc_1m_queue")

# 获取所有队列配置
all_configs = fetcher_queue_manager.get_all_queue_configs(active_only=True)

# 更新队列配置
result = fetcher_queue_manager.update_queue_config(
    "btc_1m_queue",
    description="更新后的描述"
)

# 激活/停用队列
fetcher_queue_manager.activate_queue("btc_1m_queue")
fetcher_queue_manager.deactivate_queue("btc_1m_queue")

# 删除队列配置
fetcher_queue_manager.delete_queue_config("btc_1m_queue")
```

## 🔒 安全特性

1. **混合加密**: 所有API请求和响应都使用混合加密（AES+RSA）
2. **签名验证**: 请求包含签名验证机制
3. **安全头部**: 需要正确的安全头部验证
4. **业务约束**: 激活状态的队列有操作限制
5. **安全创建**: 队列创建时强制为不激活状态，前端无法绕过此限制
6. **权限分离**: 激活/停用队列需要使用专门的端点，与创建/更新端点分离

## 📝 示例数据

系统包含以下示例队列配置：
- `btc_1m_kline`: BTC/USDT 1分钟K线
- `eth_1m_kline`: ETH/USDT 1分钟K线
- `btc_5m_kline`: BTC/USDT 5分钟K线
- `eth_5m_kline`: ETH/USDT 5分钟K线
- `bnb_1h_kline`: BNB/USDT 1小时K线

## 🧪 测试

运行测试脚本验证功能：
```bash
cd /path/to/project/app
python3 test_queue_api.py        # API导入和数据库连接测试
python3 init_sample_queues.py    # 创建示例数据
python3 test_queue_config.py     # 完整功能测试
```

## 🚀 部署说明

1. **数据库表**: 表会在首次运行时自动创建
2. **API集成**: 已集成到主FastAPI应用中
3. **环境变量**: 确保数据库连接环境变量正确配置
4. **密钥管理**: 确保加密密钥正确配置

## 📋 TODO

1. 前端界面开发
2. 批量操作支持
3. 队列状态监控
4. 性能优化
5. 更多交易所支持
