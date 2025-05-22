# 测试与调试指南

本文档提供了如何测试和调试前后端安全通信的详细步骤。

## 先决条件

确保已安装所有必要的依赖：

```bash
pip install -r requirements.txt
```

## 启动服务

1. 启动后端API服务器

```bash
cd /Users/cayeho/Project/Cryp/AutoTradingBinance
uvicorn myfastapi.main:app --reload
```

2. 启动前端开发服务器

```bash
cd /Users/cayeho/Project/Cryp/AutoTradingBinance/Frontend
npm run dev
```

## 创建测试用户

使用提供的脚本创建测试用户：

```bash
cd /Users/cayeho/Project/Cryp/AutoTradingBinance
python myfastapi/create_test_user.py --uid testuser --username "测试用户"
```

该脚本将：
- 创建一个新用户
- 生成TOTP密钥
- 创建用于Google Authenticator的二维码
- 显示当前的验证码供测试使用

## 运行测试套件

执行完整的测试套件：

```bash
cd /Users/cayeho/Project/Cryp/AutoTradingBinance
bash myfastapi/run_tests.sh
```

这将依次运行：
1. 数据库连接测试
2. 安全模块功能测试
3. 检查API服务器状态
4. 前后端集成测试

## 手动测试登录

1. 访问 http://localhost:3000/login
2. 输入测试用户ID（默认为"testuser"）
3. 从Google Authenticator获取当前的6位验证码并输入
4. 点击"Verify"按钮

## 调试前端问题

在浏览器控制台中可以看到详细的请求/响应信息。关注以下几点：

1. 请求头是否包含所有必要的安全头：
   - `X-API-Key`
   - `X-Timestamp`
   - `X-Signature`

2. 请求主体是否包含：
   - `encrypted_data`
   - `timestamp`
   - `signature`

## 调试后端问题

1. 检查后端日志（fastapi.log）

```bash
tail -f /Users/cayeho/Project/Cryp/AutoTradingBinance/fastapi.log
```

2. 调试数据库连接

```bash
python myfastapi/test_database_connection.py
```

3. 测试安全模块功能

```bash
python myfastapi/test_security.py
```

## 常见问题与解决方案

### 401 Unauthorized - Missing security headers

**解决方案**：确保前端请求中包含所有必要的安全头，检查`secureApi.ts`中的请求头设置。

### 解密失败

**解决方案**：
- 确保公钥格式正确
- 检查加密/解密函数参数
- 验证前端和后端使用相同的加密算法和参数

### 签名验证失败

**解决方案**：
对于前端客户端，我们使用固定值"frontend"作为签名。后端已配置为接受此值。

### 会话过期

**解决方案**：
时间戳验证配置为60秒超时。确保前端和后端服务器时间同步，或调整超时值。

## 其他资源

更多信息，请参考：

- [安全修复文档](./docs/security_fix.md)
- [PostgreSQL安全文档](./docs/README-PostgreSQL-Security.md)
- [安全密钥管理](./docs/security_keys.md)
