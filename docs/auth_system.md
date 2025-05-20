# API 认证系统文档

## 概述

本文档详细说明了 API 认证系统的实现，包括 JWT 令牌认证、密码加密和用户验证等功能。系统提供了完整的认证流程，确保 API 访问的安全性。

关于 API 加密和签名系统的详细信息，请参见 [security_keys.md](security_keys.md)。

## 配置说明

### 环境变量配置

系统使用以下环境变量：

```bash
JWT_SECRET=your_jwt_secret_here        # JWT 签名密钥
JWT_EXPIRE_MINUTES=30                  # 令牌过期时间（分钟）
```

### 核心配置

```python
ALGORITHM = "HS256"                    # JWT 加密算法
ACCESS_TOKEN_EXPIRE_MINUTES = 30       # 默认令牌过期时间
```

## 核心功能

### 1. JWT 令牌管理

#### JWT 密钥管理
```python
def get_jwt_secret_key() -> str:
    """
    获取 JWT 密钥，优先从环境变量获取。
    如未配置环境变量，则从配置文件加载。
    """
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        from config import JWT_SECRET_KEY
        jwt_secret = JWT_SECRET_KEY
    
    if not jwt_secret:
        raise ValueError("JWT secret key is not configured")
    return jwt_secret
```

#### 令牌创建
```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT 访问令牌。
    
    示例：
    ```python
    token = create_access_token(
        data={"sub": user.id, "name": user.username},
        expires_delta=timedelta(days=1)
    )
    ```
    """
```

#### 令牌验证
```python
def verify_token(token: str) -> Dict[str, Any]:
    """
    验证 JWT 令牌的有效性。
    
    示例：
    ```python
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
    except HTTPException:
        # 处理无效令牌
    ```
    """
```

### 2. 密码管理

#### 密码验证
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证用户密码。
    
    示例：
    ```python
    if verify_password(login_password, stored_hashed_password):
        # 密码正确，继续处理
    ```
    """
```

#### 密码加密
```python
def get_password_hash(password: str) -> str:
    """
    生成密码的哈希值。
    
    示例：
    ```python
    hashed_password = get_password_hash(user_password)
    # 将 hashed_password 存储到数据库
    ```
    """
```

### 3. 用户认证

#### 当前用户获取
```python
def get_current_user(token: str) -> Dict[str, Any]:
    """
    从 JWT 令牌中获取当前用户信息。
    
    示例：
    ```python
    @app.get("/users/me")
    async def get_user_info(token: str = Depends(oauth2_scheme)):
        user = get_current_user(token)
        return user
    ```
    """
```

## 使用示例

### 1. 用户登录流程

```python
@app.post("/login")
async def login(username: str, password: str):
    # 1. 从数据库获取用户
    user = get_user_from_db(username)
    
    # 2. 验证密码
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # 3. 创建访问令牌
    access_token = create_access_token(
        data={"sub": user.id, "username": user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
```

### 2. 受保护的 API 端点

```python
@app.get("/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    try:
        # 获取当前用户
        current_user = get_current_user(token)
        return {"message": "Welcome", "user": current_user}
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
```

## 安全性考虑

1. **密钥管理**
   - JWT 密钥必须保持安全
   - 建议使用环境变量存储敏感信息
   - 定期轮换密钥

2. **令牌安全**
   - 默认令牌过期时间为 30 分钟
   - 可通过环境变量 `JWT_EXPIRE_MINUTES` 调整
   - 包含令牌创建时间戳（iat）用于额外验证

3. **密码安全**
   - 使用 bcrypt 进行密码哈希
   - 自动处理加盐和迭代次数
   - 永不存储明文密码

## 错误处理

系统使用标准的 HTTP 状态码：

- 401 Unauthorized：认证失败
  - 无效的令牌
  - 令牌过期
  - 密码错误
  
- 500 Internal Server Error：服务器错误
  - 密钥配置错误
  - 令牌创建失败

所有错误都会记录到日志系统中，便于问题诊断。
