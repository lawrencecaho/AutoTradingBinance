# 环境配置变量对照表

## 📊 配置变量整合前后对比

### 整合前的配置分布

| 变量名 | .env | .env.production | .env.example |
|--------|------|-----------------|--------------|
| DATABASE_URL | ✅ | ✅ | ❌ |
| REDIS_URL | ✅ | ✅ | ❌ |
| REDIS_PASSWORD | ✅ | ✅ | ❌ |
| REDIS_DB | ✅ | ✅ | ❌ |
| JWT_EXPIRE_MINUTES | ✅ | ❌ | ✅ |
| REFRESH_TOKEN_EXPIRE_DAYS | ✅ | ❌ | ✅ |
| ENVIRONMENT | ❌ | ❌ | ✅ |
| USE_HTTPS | ❌ | ❌ | ✅ |
| COOKIE_DOMAIN | ❌ | ❌ | ✅ |

### 整合后的配置分布

| 变量名 | .env | .env.production | .env.example |
|--------|------|-----------------|--------------|
| **环境配置** | | | |
| ENVIRONMENT | ✅ (development) | ✅ (production) | ✅ (模板) |
| USE_HTTPS | ✅ (false) | ✅ (true) | ✅ (模板) |
| COOKIE_DOMAIN | ✅ (空) | ✅ (caho.cc) | ✅ (模板) |
| **数据库配置** | | | |
| DATABASE_URL | ✅ (开发) | ✅ (生产) | ✅ (模板) |
| **Redis配置** | | | |
| REDIS_URL | ✅ (开发) | ✅ (生产) | ✅ (模板) |
| REDIS_PASSWORD | ✅ | ✅ | ✅ (模板) |
| REDIS_DB | ✅ | ✅ | ✅ (模板) |
| **认证配置** | | | |
| JWT_EXPIRE_MINUTES | ✅ (60) | ✅ (15) | ✅ (模板) |
| REFRESH_TOKEN_EXPIRE_DAYS | ✅ (7) | ✅ (7) | ✅ (模板) |
| JWT_SECRET | ✅ (开发) | ✅ (生产) | ✅ (模板) |
| CSRF_EXPIRE_SECONDS | ✅ | ✅ | ✅ (模板) |
| **网络配置** | | | |
| ALLOWED_ORIGINS | ✅ (本地) | ✅ (域名) | ✅ (模板) |
| RATE_LIMIT_REQUESTS | ✅ (200) | ✅ (50) | ✅ (模板) |
| RATE_LIMIT_WINDOW | ✅ | ✅ | ✅ (模板) |
| **日志配置** | | | |
| LOG_LEVEL | ✅ (DEBUG) | ✅ (WARNING) | ✅ (模板) |
| **交易API** | | | |
| BINANCE_API_KEY | ✅ (测试) | ✅ (生产) | ✅ (模板) |
| BINANCE_SECRET_KEY | ✅ (测试) | ✅ (生产) | ✅ (模板) |
| BINANCE_TESTNET | ✅ (true) | ✅ (false) | ✅ (模板) |
| **服务器配置** | | | |
| SERVER_PORT | ✅ | ✅ | ✅ (模板) |
| SERVER_HOST | ✅ | ✅ | ✅ (模板) |
| TIMEZONE | ✅ | ✅ | ✅ (模板) |

## 📈 配置改进统计

### 新增变量
- **JWT_SECRET**: 增加JWT密钥配置
- **CSRF_EXPIRE_SECONDS**: CSRF令牌过期配置
- **ALLOWED_ORIGINS**: CORS源配置
- **RATE_LIMIT_***: API速率限制配置
- **LOG_LEVEL**: 日志级别配置
- **BINANCE_***: 完整的Binance API配置
- **SERVER_***: 服务器配置
- **TIMEZONE**: 时区配置

### 环境差异化
| 配置项 | 开发环境 | 生产环境 | 差异说明 |
|--------|----------|----------|----------|
| ENVIRONMENT | development | production | 环境标识 |
| USE_HTTPS | false | true | HTTPS强制 |
| COOKIE_DOMAIN | 空 | caho.cc | 域名绑定 |
| JWT_EXPIRE_MINUTES | 60 | 15 | 安全性vs便利性 |
| JWT_SECRET | 测试密钥 | 生产密钥 | 安全密钥 |
| ALLOWED_ORIGINS | localhost | 域名 | CORS限制 |
| RATE_LIMIT_REQUESTS | 200 | 50 | 请求限制 |
| LOG_LEVEL | DEBUG | WARNING | 日志详细度 |
| BINANCE_TESTNET | true | false | 测试vs生产 |
| SERVER_HOST | 127.0.0.1 | 0.0.0.0 | 网络访问 |

## 🔄 迁移检查清单

### 从旧配置迁移
- [ ] 备份现有 `.env` 文件
- [ ] 检查所有自定义配置值
- [ ] 更新API密钥和密码
- [ ] 验证数据库连接字符串
- [ ] 测试Redis连接
- [ ] 确认CORS源设置
- [ ] 验证Binance API配置

### 生产环境部署前
- [ ] 设置强JWT密钥
- [ ] 配置正确的域名
- [ ] 启用HTTPS
- [ ] 设置真实的API密钥
- [ ] 关闭测试网模式
- [ ] 调整日志级别
- [ ] 配置生产数据库
- [ ] 设置Redis密码

### 开发环境优化
- [ ] 启用DEBUG日志
- [ ] 使用测试网API
- [ ] 配置本地数据库
- [ ] 设置宽松的速率限制
- [ ] 允许本地CORS源

## 📝 使用建议

1. **开发阶段**: 使用 `.env` 文件
2. **测试阶段**: 使用接近生产的配置测试
3. **生产部署**: 使用 `.env.production` 文件
4. **配置管理**: 定期审查和更新配置
5. **安全审计**: 定期检查敏感配置项

## 🔗 相关文档

- [环境配置使用说明](ENV_CONFIG_GUIDE.md)
- [安全配置模块](myfastapi/security_config.py)
- [安全修复报告](SECURITY_FIX_REPORT.md)
