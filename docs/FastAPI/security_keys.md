# API 安全密钥系统文档

## 密钥系统概述

系统使用两个主要的密钥：
1. `ENCRYPTION_KEY`：用于 Fernet 对称加密
2. `API_SECRET_KEY`：用于 HMAC-SHA256 签名验证

## 密钥配置

### 环境变量配置

系统优先从环境变量获取密钥：

```bash
ENCRYPTION_KEY=your_encryption_key_here    # Fernet 加密密钥
API_SECRET_KEY=your_api_secret_here        # API 签名密钥
MAX_REQUEST_AGE_SECONDS=300                # 请求时间戳有效期（秒）
```

### 配置文件设置

如果环境变量未设置，系统会尝试从 `config.py` 加载密钥：

```python
ENCRYPTION_KEY = "your_encryption_key_here"
API_SECRET_KEY = "your_api_secret_here"
```

## 密钥处理流程

### 1. ENCRYPTION_KEY 处理

```python
def get_encryption_key() -> bytes:
    """获取加密密钥，优先从环境变量获取"""
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        try:
            from config import ENCRYPTION_KEY
            key = ENCRYPTION_KEY
        except (ImportError, AttributeError):
            return generate_fernet_key()  # 自动生成新密钥

    try:
        if isinstance(key, bytes):
            Fernet(key)  # 验证密钥有效性
            return key
        return create_valid_key(key)  # 转换为有效的 Fernet 密钥
    except Exception:
        return generate_fernet_key()  # 如果密钥无效则生成新密钥
```

特点：
- 多重回退机制
- 自动密钥生成
- 密钥格式验证和转换
- 错误处理和日志记录

### 2. API_SECRET_KEY 处理

```python
def get_api_secret() -> bytes:
    """获取 API 密钥，优先从环境变量获取"""
    secret = os.getenv("API_SECRET_KEY")
    if not secret:
        try:
            from config import API_SECRET_KEY
            secret = API_SECRET_KEY
        except (ImportError, AttributeError):
            raise ValueError("API secret key not configured")

    return secret.encode() if isinstance(secret, str) else secret
```

特点：
- 必须配置，无自动生成
- 支持字符串和字节格式
- 严格的错误处理

## 安全机制

### 1. Fernet 加密系统

使用 `cryptography.fernet` 进行对称加密：
- 安全的密钥生成
- 加密和解密操作
- 自动处理密钥编码

### 2. 签名验证系统

使用 HMAC-SHA256 进行请求签名：
```python
def generate_signature(data: str, timestamp: str) -> str:
    message = f"{data}{timestamp}".encode()
    signature = hmac.new(API_SECRET_KEY, message, hashlib.sha256).hexdigest()
    return signature
```

### 3. 时间戳验证

防止重放攻击：
- 验证请求时间戳
- 默认 5 分钟有效期
- 可配置的超时设置

## 最佳实践

1. **密钥管理**
   - 使用环境变量存储密钥
   - 定期轮换密钥
   - 不同环境使用不同密钥

2. **安全配置**
   - `ENCRYPTION_KEY` 应使用强随机生成
   - `API_SECRET_KEY` 应足够长且复杂
   - 合理设置请求超时时间

3. **错误处理**
   - 所有错误都记录到日志
   - 提供明确的错误信息
   - 保护敏感信息不泄露

## 状态码说明

- **400 Bad Request**
  - 无效的加密数据
  - 请求已过期
  - 时间戳格式错误

- **401 Unauthorized**
  - 签名验证失败

- **500 Internal Server Error**
  - 加密失败
  - 签名生成失败
  - Fernet 初始化失败

## 调试信息

可通过 `/security-info` 端点获取安全配置信息：
```json
{
    "encryption_key": "<base64_encoded_key>",
    "signature_format": "HMAC-SHA256(data + timestamp, API_SECRET_KEY)",
    "timestamp_format": "milliseconds since epoch",
    "max_age": 300000
}
```

## 注意事项

1. 永远不要在客户端存储 `API_SECRET_KEY`
2. `ENCRYPTION_KEY` 只在服务器间通信时使用
3. 所有密钥相关的错误都会记录在日志中
4. 定期检查日志以发现潜在的安全问题
