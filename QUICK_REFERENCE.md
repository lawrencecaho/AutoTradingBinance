# AutoTradingBinance 快速参考

## 🎯 核心问题解答

### 这个项目是做什么的？

AutoTradingBinance 是一个**币安加密货币自动交易系统**，能够：
- 自动从币安获取市场数据
- 基于策略自动执行交易
- 提供安全的 Web API 接口
- 支持多交易对管理

### 主要程序是什么？

#### 1️⃣ **Web API 服务器** - `app/myfastapi/main.py`
   - **作用**：提供 RESTful API 接口
   - **功能**：用户认证、数据查询、队列管理
   - **启动**：`uvicorn myfastapi.main:app --port 8000`
   - **特点**：RSA 加密通信、JWT 认证、TOTP 双因素认证

#### 2️⃣ **项目管理器** - `app/manage.py` 和 `app/ProgramManager/shell.py`
   - **作用**：交互式项目管理工具
   - **功能**：环境设置、依赖管理、服务器管理、安全检查
   - **启动**：`python app/manage.py`
   - **特点**：彩色交互界面、一键式操作

#### 3️⃣ **主应用入口** - `app/main.py`
   - **作用**：生产环境应用启动入口
   - **功能**：队列设置、K 线数据获取、交易信号生成
   - **启动**：直接运行或通过管理器启动

#### 4️⃣ **数据获取器** - `app/ExchangeFetcher/fetcher.py`
   - **作用**：从币安获取市场数据
   - **功能**：实时价格、K 线数据、WebSocket 监控
   - **支持**：多交易对、多时间周期（1m, 5m, 1h, 1d 等）

#### 5️⃣ **交易执行器** - `app/trader.py` 和 `app/ExchangeBill/`
   - **作用**：执行交易决策
   - **功能**：订单构造、订单提交、交易记录
   - **接口**：与币安 API 交互，支持 RSA 签名

#### 6️⃣ **策略模块** - `app/strategy.py`
   - **作用**：定义和执行交易策略
   - **功能**：信号生成、策略参数配置
   - **扩展**：可自定义添加新策略

#### 7️⃣ **数据分析** - `app/DataProcessingCalculator/`
   - **作用**：市场数据分析和计算
   - **功能**：技术指标、趋势分析、数据质量评估

## 🚀 30 秒快速启动

```bash
# 1. 启动项目管理器
python app/manage.py

# 2. 在管理界面输入命令
setup        # 完整环境设置
status       # 检查系统状态
server       # 启动 API 服务器

# 3. 或直接启动 API 服务器
uvicorn myfastapi.main:app --host 0.0.0.0 --port 8000 --reload
```

## 📁 关键目录

```
app/
├── myfastapi/              # 🌐 Web API 后端（主程序）
├── ExchangeFetcher/        # 📊 数据获取
├── ExchangeBill/           # 💰 订单和交易
├── DataProcessingCalculator/  # 📈 数据分析
├── DesisionMaker/          # 🤔 决策制定
├── ProgramManager/         # 🔧 项目管理工具（主程序）
├── DatabaseOperator/       # 🗄️ 数据库操作
├── WorkLine/               # ⚙️ 工作流管理
├── main.py                 # 🚀 应用入口（主程序）
├── manage.py               # 🛠️ 管理器入口（主程序）
├── strategy.py             # 📋 交易策略（主程序）
└── trader.py               # 🎯 交易执行（主程序）
```

## 🔑 核心技术

- **后端框架**：FastAPI（异步高性能）
- **数据库**：PostgreSQL + SQLAlchemy
- **缓存**：Redis（会话、Token 管理）
- **加密**：RSA-2048、JWT、bcrypt
- **交易 API**：python-binance
- **数据处理**：pandas、numpy

## 📚 主要功能

1. **安全的 Web API** - 加密通信、双因素认证
2. **实时数据采集** - 从币安获取价格和 K 线数据
3. **自动交易执行** - 基于策略自动下单
4. **队列管理** - 灵活配置多个数据获取队列
5. **数据分析** - 技术指标计算和趋势分析
6. **交互式管理** - 便捷的项目管理工具

## 🔗 相关文档

- **完整文档**：[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) - 详细的项目说明
- **基本说明**：[README.md](./README.md) - 项目基本信息
- **队列 API**：[app/QUEUE_API_DOCUMENTATION.md](./app/QUEUE_API_DOCUMENTATION.md) - 队列管理 API
- **管理工具**：[app/ProgramManager/README.md](./app/ProgramManager/README.md) - 管理器说明

## 💡 常用命令

```bash
# 启动管理器
python app/manage.py

# 启动 API 服务器
uvicorn myfastapi.main:app --port 8000 --reload

# Redis 管理
python app/ProgramManager/redis_manager.py test

# 安全检查
./security_check.sh

# 查看帮助
python app/manage.py  # 然后输入 help
```

## ⚠️ 重要提示

1. **首次使用**：先运行 `python app/manage.py`，然后选择 `setup` 进行环境设置
2. **配置文件**：复制 `.env.example` 到 `.env` 并填写配置
3. **测试环境**：建议先在币安测试网测试
4. **API 密钥**：妥善保管，不要泄露或提交到代码库

---

**更多详细信息请参阅 [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)**
