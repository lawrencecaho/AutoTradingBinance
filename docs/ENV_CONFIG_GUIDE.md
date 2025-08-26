# 环境配置文件使用说明

## 📁 配置文件结构

项目现在包含三个环境配置文件：

- `.env.example` - 配置模板文件，包含所有可能的环境变量
- `.env` - 开发环境配置文件
- `.env.production` - 生产环境配置文件

## 🔧 配置变量说明

### 环境配置
- `ENVIRONMENT`: 环境类型 (development/production)
- `USE_HTTPS`: 是否启用HTTPS
- `COOKIE_DOMAIN`: Cookie域名设置

### 数据库配置
- `DATABASE_URL`: PostgreSQL数据库连接字符串

### Redis配置
- `REDIS_URL`: Redis服务器地址
- `REDIS_PASSWORD`: Redis密码
- `REDIS_DB`: Redis数据库编号

### 认证和安全
- `JWT_EXPIRE_MINUTES`: JWT令牌过期时间（分钟）
- `REFRESH_TOKEN_EXPIRE_DAYS`: 刷新令牌过期时间（天）
- `JWT_SECRET`: JWT签名密钥
- `CSRF_EXPIRE_SECONDS`: CSRF令牌过期时间（秒）

### 网络配置
- `ALLOWED_ORIGINS`: 允许的CORS源
- `RATE_LIMIT_REQUESTS`: 速率限制请求数
- `RATE_LIMIT_WINDOW`: 速率限制时间窗口

### 日志配置
- `LOG_LEVEL`: 日志级别 (DEBUG/INFO/WARNING/ERROR)

### 交易API
- `BINANCE_API_KEY`: Binance API密钥
- `BINANCE_SECRET_KEY`: Binance API私钥
- `BINANCE_TESTNET`: 是否使用测试网

### 服务器配置
- `SERVER_PORT`: 服务器端口
- `SERVER_HOST`: 服务器主机
- `TIMEZONE`: 时区设置

## 🚀 使用方法

### 开发环境
```bash
# 使用开发环境配置
cp .env.example .env
# 然后编辑 .env 文件设置开发环境的值
```

### 生产环境
```bash
# 使用生产环境配置
cp .env.production .env
# 或者在部署时直接使用 .env.production
```

### Docker部署
```bash
# 在docker-compose.yml中指定环境文件
env_file:
  - .env.production
```

## ⚠️ 安全注意事项

### 开发环境
- JWT过期时间较长 (60分钟)
- 日志级别为DEBUG
- 使用测试网API
- 较宽松的速率限制

### 生产环境
- JWT过期时间较短 (15分钟)
- 日志级别为WARNING
- 使用真实API
- 严格的速率限制
- 强制HTTPS
- 设置Cookie域名

### 密钥管理
1. **JWT_SECRET**: 生产环境必须使用强密钥
2. **数据库密码**: 使用强密码并定期更换
3. **Redis密码**: 设置强密码
4. **API密钥**: 妥善保管Binance API密钥

## 🔄 配置迁移

如果需要从旧配置迁移：

1. 备份现有的 `.env` 文件
2. 使用新的 `.env.example` 作为模板
3. 逐项迁移配置值
4. 测试新配置是否正常工作

## 📝 配置验证

使用以下脚本验证配置：

```bash
python3 security_verification.py
```

这将检查：
- 所有必需的环境变量是否设置
- 生产环境的安全配置是否正确
- 配置值是否合理

## 🔗 相关文档

- [安全配置指南](SECURITY_FIX_REPORT.md)
- [部署说明](README.md)
- [安全审计报告](SECURITY_AUDIT_REPORT.md)
