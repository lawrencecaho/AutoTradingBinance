# AutoTradingBinance 项目概览

## 📋 项目简介

**AutoTradingBinance** 是一个基于 Python 的币安（Binance）加密货币自动交易系统，集成了安全的 Web API 后端、数据采集、策略分析和交易执行等完整功能。

## 🎯 项目核心目标

1. **自动化交易**: 实现加密货币的自动化交易策略执行
2. **数据采集**: 实时获取和存储加密货币市场数据
3. **安全通信**: 提供安全的 API 接口，支持 RSA 加密和双因素认证
4. **策略分析**: 基于历史数据和实时数据进行交易决策
5. **交易管理**: 完整的订单管理和交易历史记录

## 🏗️ 项目架构

```
AutoTradingBinance/
├── app/                          # 主应用目录
│   ├── main.py                   # 应用主入口（生产环境）
│   ├── manage.py                 # 项目管理入口
│   ├── myfastapi/                # FastAPI Web 后端
│   │   ├── main.py              # FastAPI 应用主文件
│   │   ├── security.py          # 加密和安全模块
│   │   ├── auth.py              # JWT 认证模块
│   │   ├── authtotp.py          # TOTP 双因素认证
│   │   ├── queue.py             # 队列管理 API
│   │   └── redis_client.py      # Redis 客户端
│   ├── DatabaseOperator/         # 数据库操作模块
│   ├── ExchangeFetcher/          # 交易所数据获取模块
│   │   ├── fetcher.py           # 数据获取器
│   │   └── realtime_monitor.py  # 实时监控
│   ├── ExchangeBill/             # 订单和交易管理
│   │   ├── orderComposerBinance.py  # 订单构造器
│   │   └── BinanceActivity_RSA.py   # Binance API 交互
│   ├── DataProcessingCalculator/ # 数据处理和计算
│   │   ├── calculator.py        # 计算模块
│   │   ├── DataAnalyze.py       # 数据分析
│   │   └── TimeDispersionAmzTool.py # 时间离散度分析
│   ├── DesisionMaker/            # 决策制定模块
│   │   └── QueueStart.py        # 队列启动
│   ├── WorkLine/                 # 工作流管理
│   │   ├── master.py            # 主控制器
│   │   └── StartSettingSet.py   # 启动设置
│   ├── ProgramManager/           # 项目管理工具集
│   │   ├── shell.py             # 交互式管理界面
│   │   ├── redis_manager.py     # Redis 管理工具
│   │   └── *.sh                 # 各种管理脚本
│   ├── strategy.py               # 交易策略模块
│   └── trader.py                 # 交易执行模块
├── docs/                         # 文档目录
├── requirements.txt              # Python 依赖
└── .env.example                  # 环境变量示例

```

## 🔑 主要程序说明

### 1. **主入口程序**

#### `app/main.py` - 生产环境主入口
- **作用**: 生产环境的应用启动入口
- **功能**:
  - 设置队列配置（`QueueSettings`）
  - 异步获取 K 线数据（`kline_rollfetch`）
  - 交易信号生成（`FortunepointFounder`）
  - 启动 FastAPI 服务器
- **启动方式**: 
  ```bash
  uvicorn myfastapi.main:app --host 0.0.0.0 --port 8000 --reload
  ```

#### `app/manage.py` - 项目管理器启动入口
- **作用**: 提供交互式项目管理界面
- **启动方式**:
  ```bash
  python app/manage.py
  ```

### 2. **FastAPI Web 后端** (`app/myfastapi/`)

#### `myfastapi/main.py` - FastAPI 应用核心
- **功能**:
  - RESTful API 端点定义
  - 用户认证和授权
  - 加密通信处理
  - 队列配置管理 API
  - 数据查询接口
- **主要端点**:
  - `/api/login` - 用户登录
  - `/api/register` - 用户注册
  - `/api/queue/edfqs/*` - 队列配置管理
  - `/api/protected/*` - 需要认证的保护接口

#### `myfastapi/security.py` - 安全模块
- **功能**:
  - RSA 加密/解密
  - 请求签名验证
  - 双向加密通信
  - 密钥管理和轮换

#### `myfastapi/auth.py` - 认证模块
- **功能**:
  - JWT Token 生成和验证
  - 用户会话管理
  - 密码加密（bcrypt）

#### `myfastapi/authtotp.py` - 双因素认证
- **功能**:
  - TOTP（Time-based One-Time Password）生成
  - Google Authenticator 兼容
  - 二维码生成

#### `myfastapi/queue.py` - 队列管理 API
- **功能**:
  - 数据获取队列配置
  - 队列激活/停用管理
  - 支持多交易对配置

### 3. **数据获取模块** (`app/ExchangeFetcher/`)

#### `ExchangeFetcher/fetcher.py` - 数据获取器
- **功能**:
  - 从 Binance 获取实时价格
  - 获取 K 线（蜡烛图）数据
  - 支持多种时间周期（1m, 5m, 1h, 1d 等）
- **主要方法**:
  - `fetch_price(symbol)` - 获取实时价格
  - `get_kline(symbol, interval)` - 获取 K 线数据

#### `ExchangeFetcher/realtime_monitor.py` - 实时监控
- **功能**:
  - WebSocket 实时数据流
  - 价格变动监控
  - 市场深度数据

### 4. **交易执行模块** (`app/ExchangeBill/`)

#### `ExchangeBill/orderComposerBinance.py` - 订单构造器
- **功能**:
  - 构造符合 Binance API 规范的订单
  - 支持多种订单类型（市价单、限价单等）
  - 订单参数验证

#### `ExchangeBill/BinanceActivity_RSA.py` - Binance API 交互
- **功能**:
  - 使用 RSA 签名与 Binance API 通信
  - 订单提交和查询
  - 账户信息获取

### 5. **数据分析模块** (`app/DataProcessingCalculator/`)

#### `DataProcessingCalculator/calculator.py` - 计算模块
- **功能**:
  - 技术指标计算
  - 价格差异分析
  - 收益率计算

#### `DataProcessingCalculator/DataAnalyze.py` - 数据分析
- **功能**:
  - 历史数据统计分析
  - 趋势识别
  - 异常检测

#### `DataProcessingCalculator/TimeDispersionAmzTool.py` - 时间离散度分析
- **功能**:
  - 数据表时间离散度分析
  - 数据质量评估
  - 采样频率优化建议

### 6. **决策制定模块** (`app/DesisionMaker/`)

#### `DesisionMaker/QueueStart.py` - 决策队列
- **功能**:
  - 基于队列的决策处理
  - 异步决策执行
  - 决策结果记录

### 7. **交易策略模块**

#### `app/strategy.py` - 策略模块
- **功能**:
  - 定义交易策略逻辑
  - 策略参数配置
  - 信号生成

#### `app/trader.py` - 交易执行器
- **功能**:
  - 执行交易决策
  - 订单提交
  - 交易记录
- **主要方法**:
  - `execute_trade(decision, quantity)` - 执行交易

### 8. **数据库操作模块** (`app/DatabaseOperator/`)

- **功能**:
  - PostgreSQL 数据库操作
  - Redis 缓存操作
  - 数据表管理
- **主要数据表**:
  - `price_{symbol}` - 价格记录表
  - `price_diff_{symbol}` - 价格差异表
  - `buy_history_{symbol}` - 买入历史表
  - `fetcher_queue_configs` - 队列配置表

### 9. **项目管理工具** (`app/ProgramManager/`)

#### `ProgramManager/shell.py` - 交互式管理界面
- **功能**:
  - 项目设置和配置
  - 依赖管理
  - 安全检查
  - 密钥管理
  - Redis 管理
  - 服务器启动/停止
  - 系统监控
  - 日志查看
- **启动方式**:
  ```bash
  python app/manage.py
  # 或
  python app/ProgramManager/shell.py
  ```

#### `ProgramManager/redis_manager.py` - Redis 管理工具
- **功能**:
  - Redis 连接测试
  - 性能统计
  - 实时监控
  - 数据清理
- **使用方式**:
  ```bash
  python app/ProgramManager/redis_manager.py test
  python app/ProgramManager/redis_manager.py monitor
  ```

## 🔄 系统工作流程

### 典型交易流程

1. **数据采集**
   - `ExchangeFetcher` 从 Binance 获取实时价格和 K 线数据
   - 数据存储到 PostgreSQL 数据库

2. **数据处理**
   - `DataProcessingCalculator` 计算技术指标和价格差异
   - `TimeDispersionAmzTool` 分析数据质量

3. **决策生成**
   - `strategy.py` 基于数据和指标生成交易信号
   - `DesisionMaker` 处理决策队列

4. **交易执行**
   - `trader.py` 接收决策信号
   - `ExchangeBill` 构造并提交订单到 Binance

5. **记录和监控**
   - 交易结果存储到数据库
   - `realtime_monitor` 实时监控市场和持仓

## 🛠️ 技术栈

### 后端技术
- **Web 框架**: FastAPI (现代异步 Python Web 框架)
- **数据库**: PostgreSQL (关系型数据库) + SQLAlchemy
- **缓存**: Redis (会话管理、Token 黑名单)
- **加密**: RSA-2048 加密、JWT Token
- **认证**: TOTP 双因素认证、bcrypt 密码加密

### 交易相关
- **交易所 API**: python-binance
- **数据处理**: pandas, numpy
- **WebSocket**: websockets (实时数据流)

### 开发工具
- **异步框架**: asyncio, uvicorn
- **环境管理**: python-dotenv
- **日志**: Python logging

## 📊 数据库设计

### 核心数据表

1. **Price 表** (`price_{symbol}`)
   - `id`: 主键
   - `symbol`: 交易对符号
   - `price`: 价格
   - `timestamp`: 记录时间

2. **PriceDiff 表** (`price_diff_{symbol}`)
   - `id`: 主键
   - `diff`: 价格差值
   - `current_price`: 当前价格
   - `buy_price`: 买入价格
   - `timestamp`: 记录时间

3. **BuyHistory 表** (`buy_history_{symbol}`)
   - `id`: 主键
   - `price`: 买入价格
   - `quantity`: 买入数量
   - `timestamp`: 记录时间

4. **FetcherQueueConfigs 表** (`fetcher_queue_configs`)
   - `id`: UUID 主键
   - `queue_name`: 队列名称（唯一）
   - `symbol`: 交易对符号
   - `exchange`: 交易所名称
   - `interval`: K 线周期
   - `is_active`: 激活状态
   - `description`: 描述
   - `created_at` / `updated_at`: 时间戳

## 🚀 快速启动

### 1. 环境设置

```bash
# 克隆仓库
git clone <repository-url>
cd AutoTradingBinance

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入必要的配置
```

### 2. 配置 `.env` 文件

```bash
# 数据库配置
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/dbname

# Redis 配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password

# 安全配置
JWT_SECRET=your_jwt_secret_key
API_SECRET_KEY=your_api_secret_key

# Binance API（可选）
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret
```

### 3. 使用项目管理器

```bash
# 启动交互式管理界面
python app/manage.py

# 在管理界面中：
# 1. 运行 'setup' 进行完整设置
# 2. 运行 'status' 检查系统状态
# 3. 运行 'server' 启动 API 服务器
```

### 4. 启动 API 服务器

```bash
# 方式 1: 直接启动
uvicorn myfastapi.main:app --host 0.0.0.0 --port 8000 --reload

# 方式 2: 通过 main.py 启动
python app/main.py

# 方式 3: 通过管理界面启动
python app/manage.py
# 然后选择 'server' 选项
```

## 🔐 安全特性

1. **RSA 加密通信**
   - 客户端-服务器双向加密
   - 请求和响应都加密
   - 防止中间人攻击

2. **双因素认证（2FA）**
   - TOTP 基于时间的一次性密码
   - 兼容 Google Authenticator
   - 增强账户安全

3. **JWT Token 认证**
   - 无状态认证机制
   - Token 过期和刷新
   - Redis Token 黑名单

4. **密钥管理**
   - 自动密钥轮换（30 天）
   - 安全的密钥存储
   - 权限控制

5. **请求验证**
   - 时间戳验证（防重放攻击）
   - 签名验证
   - CSRF 保护

## 📖 API 文档

### 认证接口

- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录
- `POST /api/refresh` - 刷新 Token
- `POST /api/logout` - 用户登出

### 队列管理接口

- `GET /api/queue/edfqs/list` - 获取所有队列配置
- `GET /api/queue/edfqs/{queue_name}` - 获取特定队列
- `POST /api/queue/edfqs/create` - 创建队列配置
- `PUT /api/queue/edfqs/{queue_name}` - 更新队列配置
- `POST /api/queue/edfqs/{queue_name}/activate` - 激活队列
- `POST /api/queue/edfqs/{queue_name}/deactivate` - 停用队列
- `DELETE /api/queue/edfqs/{queue_name}/delete` - 删除队列

### 数据查询接口

- `GET /api/protected/data` - 获取市场数据
- `GET /api/protected/history` - 获取历史数据

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
cd app/myfastapi
./run_tests.sh

# 测试 Redis 连接
python app/ProgramManager/test_redis.py

# 测试双向加密
python app/myfastapi/demo_bidirectional_encryption.py
```

### 安全检查

```bash
# 运行安全检查
./security_check.sh

# 设置安全权限
sudo ./secure_permissions.sh
```

## 📝 开发指南

### 添加新的交易策略

1. 在 `app/strategy.py` 中定义策略逻辑
2. 在 `app/DesisionMaker/` 中集成决策流程
3. 使用 `app/trader.py` 执行交易

### 添加新的数据源

1. 在 `app/ExchangeFetcher/` 中添加新的获取器
2. 配置队列管理（使用队列 API）
3. 在数据库中创建相应的数据表

### 添加新的 API 端点

1. 在 `app/myfastapi/main.py` 中定义路由
2. 实现请求验证和加密处理
3. 添加相应的数据库操作

## 🔧 管理工具

### 交互式管理界面功能

通过 `python app/manage.py` 启动，提供以下功能：

1. **项目设置** - 完整环境设置
2. **依赖管理** - 安装和更新依赖
3. **安全管理** - 安全检查和权限设置
4. **密钥管理** - 密钥检查和轮换
5. **Redis 管理** - Redis 连接、监控和测试
6. **服务器管理** - 启动/停止 API 服务器
7. **系统监控** - 资源使用监控
8. **项目状态** - 检查所有组件状态
9. **日志查看** - 查看系统日志

## 📚 相关文档

- [README.md](./README.md) - 项目基本说明
- [docs/README-PostgreSQL-Security.md](./docs/README-PostgreSQL-Security.md) - PostgreSQL 安全模块
- [docs/testing_guide.md](./docs/testing_guide.md) - 测试指南
- [docs/security_guide.md](./docs/security_guide.md) - 安全指南
- [app/QUEUE_API_DOCUMENTATION.md](./app/QUEUE_API_DOCUMENTATION.md) - 队列 API 文档
- [app/ProgramManager/README.md](./app/ProgramManager/README.md) - 项目管理器说明

## ⚠️ 注意事项

1. **测试环境**: 在生产环境使用前，务必在测试环境充分测试
2. **API 密钥**: 妥善保管 Binance API 密钥，不要提交到版本控制
3. **资金安全**: 建议使用 Binance 测试网进行初期测试
4. **风险控制**: 设置合理的止损和仓位管理
5. **日志监控**: 定期检查日志，及时发现和处理异常

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

请参阅项目许可证文件。

---

**本项目仅供学习和研究使用，交易有风险，投资需谨慎！**
