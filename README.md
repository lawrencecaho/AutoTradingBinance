# PostgreSQL兼容的加密通信系统

本项目实现了一个基于FastAPI的安全API后端与Next.js前端，提供RSA加密通信、OTP认证和JWT授权功能。系统已针对PostgreSQL进行优化，使用SQLAlchemy Core进行数据库操作。

## 主要功能

- **安全通信**：使用RSA加密保护客户端与服务器之间的通信
- **双因素认证**：支持基于TOTP (Google Authenticator) 的验证
- **数据库兼容性**：优化的PostgreSQL支持，使用SQLAlchemy Core
- **双向加密**：实现了完整的双向加密通信机制，请求和响应都经过加密
- **安全工具**：提供了安全检查和权限设置工具
- **密钥管理**：自动密钥轮换和同步机制
- **前端集成**：安全的Next.js前端实现

## 快速开始

### 环境设置

1. 克隆仓库并安装依赖

```bash
git clone <repository-url>
cd AutoTradingBinance
pip install -r requirements.txt
cd Frontend
npm install
cd ..
```

2. 设置环境变量

创建`.env`文件并添加必要的环境变量：

```
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/dbname
JWT_SECRET=your_jwt_secret_key
API_SECRET_KEY=your_api_secret_key
```

3. 使用快速启动脚本

```bash
./quick_start.sh
```

这将执行以下操作：
- 创建测试用户和TOTP密钥
- 显示如何启动API服务器和前端开发服务器的指令
- 提供登录信息

## 组件说明

### 后端 (FastAPI)

- **security.py**: 处理加密、解密和签名验证
- **auth.py**: JWT令牌生成和验证
- **authtotp.py**: TOTP验证码生成和验证
- **main.py**: API端点定义和请求处理

### 前端 (Next.js)

- **crypto.ts**: 加密工具函数
- **secureApi.ts**: 加密通信实现
- **AuthContext.tsx**: 认证状态管理
- **login/page.tsx**: 登录页面实现

## 测试与调试

详细的测试指南请参考 [测试指南](./docs/testing_guide.md)。

简要步骤：

1. 运行测试套件：

```bash
bash myfastapi/run_tests.sh
```

2. 手动测试登录：

- 启动后端：`uvicorn myfastapi.main:app --reload`
- 启动前端：`cd Frontend && npm run dev`
- 访问：http://localhost:3000/login

## 安全说明

本系统已实施以下安全措施：

- 服务器端使用RSA-2048加密
- 支持密钥自动轮换（每30天）
- 请求包含时间戳以防止重放攻击
- 数据库存储的密码使用bcrypt加密

## 技术文档

- [PostgreSQL安全模块文档](./docs/README-PostgreSQL-Security.md)
- [安全修复记录](./docs/security_fix.md)
- [密钥管理说明](./docs/security_keys.md)
- [测试指南](./docs/testing_guide.md)

## 近期更新

- 修复了安全头验证问题
- 增强了前端错误处理
- 添加了测试用户创建脚本
- 改进了数据库连接与事务管理

字段：

id：主键，整数类型。

symbol：交易对符号，字符串类型。

price：价格，浮点数类型。

timestamp：记录时间，日期时间类型。

PriceDiff

表名格式：price_diff_{SYMBOL.lower()}

字段：

id：主键，整数类型。

diff：价格差值，浮点数类型。

current_price：当前价格，浮点数类型。

buy_price：买入价格，浮点数类型。

timestamp：记录时间，日期时间类型。

BuyHistory

表名格式：buy_history_{SYMBOL.lower()}

字段：

id：主键，整数类型。

price：买入价格，浮点数类型。

quantity：买入数量，浮点数类型。

timestamp：记录时间，日期时间类型。

## 变量
current_price

类型：Price 表的实例

用途：存储查询得到的最新价格记录。

last_buy

类型：BuyHistory 表的实例

用途：存储最近一次买入记录。

diff

类型：浮点数

用途：表示当前价格与最近一次买入价格之间的差值。

latest_diff

类型：PriceDiff 表的实例

用途：存储最新一条价格差异记录。

decision

类型：元组或 None

用途：存储当前交易决策，格式为 (交易类型, 当前价格)，其中交易类型为 BUY 或 SELL。

说明
所有数据表均基于交易对符号动态生成表名，以支持多交易对场景。

变量用于连接数据库记录、执行交易逻辑判断与记录决策结果。

## 安全工具

系统提供了多种安全工具，帮助维护和验证系统安全：

### 安全检查

运行安全检查脚本，验证系统安全配置：

```bash
./security_check.sh
```

这将检查密钥文件权限、环境变量配置、密钥过期状态等安全问题。

### 权限设置

设置正确的文件权限，确保密钥安全：

```bash
sudo ./secure_permissions.sh
```

### 测试工具

系统包含多种测试工具，验证功能正常：

```bash
cd myfastapi
./run_tests.sh
```

或测试双向加密功能：

```bash
python myfastapi/demo_bidirectional_encryption.py
```

### 前端测试页面

访问 `/test-encryption` 路径，测试前端双向加密功能。

## 安全文档

详细的安全文档位于 `docs` 目录：

- [安全指南](docs/security_guide.md) - 密钥管理与安全通信详解
- [响应加密](docs/response_encryption.md) - 双向加密实现说明
- [安全最佳实践](docs/security_best_practices.md) - 安全配置与部署建议
- [安全修复](docs/security_fix.md) - 近期安全修复说明

