# AutoTradingBinance 前端API集成检查清单

## 重要说明
- **所有API响应均为加密格式**，需要先解密`encrypted_data`字段才能获取实际数据
- **Token管理**：使用JWT Token进行身份验证，支持Token撤销和黑名单机制
- **基础URL**：假设为 `https://api.caho.cc`

## 1. 认证相关API

### 1.1 用户登录 - OTP验证
```
POST /api/auth/verify-otp
```

**请求体**：
```json
{
  "username": "your_username",
  "otp_code": "123456"
}
```

**成功响应**（解密后）：
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user_id": "user123"
}
```

**错误响应**（解密后）：
```json
{
  "detail": "Invalid OTP code"
}
```

**前端处理示例**：
```typescript
const login = async (username: string, otpCode: string) => {
  try {
    const response = await fetch('/api/auth/verify-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, otp_code: otpCode })
    });
    
    const encryptedData = await response.json();
    const decryptedData = await decryptResponse(encryptedData.encrypted_data);
    
    if (response.ok) {
      localStorage.setItem('access_token', decryptedData.access_token);
      return { success: true, data: decryptedData };
    } else {
      return { success: false, error: decryptedData.detail };
    }
  } catch (error) {
    return { success: false, error: 'Network error' };
  }
};
```

### 1.2 用户登出 - Token撤销
```
POST /api/auth/logout
```

**请求头**：
```
Authorization: Bearer your_jwt_token
```

**成功响应**（解密后）：
```json
{
  "message": "Successfully logged out"
}
```

**前端处理示例**：
```typescript
const logout = async () => {
  const token = localStorage.getItem('access_token');
  try {
    const response = await fetch('/api/auth/logout', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const encryptedData = await response.json();
    const decryptedData = await decryptResponse(encryptedData.encrypted_data);
    
    // 清除本地存储
    localStorage.removeItem('access_token');
    
    return { success: response.ok, message: decryptedData.message };
  } catch (error) {
    // 即使出错也要清除本地token
    localStorage.removeItem('access_token');
    return { success: false, error: 'Logout failed' };
  }
};
```

### 1.3 Token刷新
```
POST /api/auth/refresh
```

**请求头**：
```
Authorization: Bearer your_jwt_token
```

**成功响应**（解密后）：
```json
{
  "access_token": "new_jwt_token_here",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### 1.4 会话检查
```
GET /api/auth/check-session
```

**请求头**：
```
Authorization: Bearer your_jwt_token
```

**成功响应**（解密后）：
```json
{
  "valid": true,
  "user_id": "user123",
  "expires_at": "2025-06-15T15:30:00Z"
}
```

**失效响应**（解密后）：
```json
{
  "valid": false,
  "detail": "Token expired or invalid"
}
```

## 2. 健康检查API

### 2.1 Redis连接检查
```
GET /health/redis
```

**成功响应**（解密后）：
```json
{
  "status": "healthy",
  "redis_connected": true,
  "timestamp": "2025-06-15T14:30:00Z"
}
```

**失败响应**（解密后）：
```json
{
  "status": "unhealthy",
  "redis_connected": false,
  "error": "Redis connection failed",
  "timestamp": "2025-06-15T14:30:00Z"
}
```

## 3. 通用错误处理

### 3.1 常见HTTP状态码
- `200`: 成功
- `400`: 请求参数错误
- `401`: 未授权（Token无效/过期）
- `403`: 权限不足
- `422`: 数据验证失败
- `500`: 服务器内部错误

### 3.2 错误响应格式（解密后）
```json
{
  "detail": "具体错误信息",
  "error_code": "OPTIONAL_ERROR_CODE",
  "timestamp": "2025-06-15T14:30:00Z"
}
```

### 3.3 前端错误处理建议
```typescript
const handleApiError = (status: number, errorData: any) => {
  switch (status) {
    case 401:
      // Token过期，重定向到登录页
      localStorage.removeItem('access_token');
      window.location.href = '/login';
      break;
    case 403:
      // 权限不足
      showNotification('权限不足', 'error');
      break;
    case 422:
      // 数据验证失败
      showFormErrors(errorData.detail);
      break;
    case 500:
      // 服务器错误
      showNotification('服务器错误，请稍后重试', 'error');
      break;
    default:
      showNotification(errorData.detail || '未知错误', 'error');
  }
};
```

## 4. 加密响应处理

### 4.1 响应解密流程
所有API响应都包含`encrypted_data`字段，需要使用RSA私钥解密：

```typescript
// 解密响应数据的通用函数
const decryptResponse = async (encryptedData: string): Promise<any> => {
  try {
    // 使用您的RSA私钥解密
    const decryptedString = await rsaDecrypt(encryptedData, privateKey);
    return JSON.parse(decryptedString);
  } catch (error) {
    console.error('解密失败:', error);
    throw new Error('数据解密失败');
  }
};

// API调用的通用包装函数
const apiCall = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('access_token');
  
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  try {
    const response = await fetch(url, {
      ...options,
      headers
    });
    
    const encryptedResponse = await response.json();
    const decryptedData = await decryptResponse(encryptedResponse.encrypted_data);
    
    return {
      ok: response.ok,
      status: response.status,
      data: decryptedData
    };
  } catch (error) {
    throw new Error(`API调用失败: ${error.message}`);
  }
};
```

## 5. Token管理最佳实践

### 5.1 Token存储
```typescript
// 安全存储Token
const storeToken = (token: string) => {
  localStorage.setItem('access_token', token);
  // 可选：设置Token过期时间提醒
  const expiresAt = Date.now() + (3600 * 1000); // 1小时后
  localStorage.setItem('token_expires_at', expiresAt.toString());
};

// 检查Token是否即将过期
const isTokenExpiringSoon = (): boolean => {
  const expiresAt = localStorage.getItem('token_expires_at');
  if (!expiresAt) return true;
  
  const timeLeft = parseInt(expiresAt) - Date.now();
  return timeLeft < (5 * 60 * 1000); // 少于5分钟
};
```

### 5.2 自动Token刷新
```typescript
const refreshTokenIfNeeded = async () => {
  if (isTokenExpiringSoon()) {
    try {
      const result = await apiCall('/api/auth/refresh', { method: 'POST' });
      if (result.ok) {
        storeToken(result.data.access_token);
      }
    } catch (error) {
      // 刷新失败，重定向到登录页
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
  }
};
```

## 6. 未实现/预留API端点

以下API端点在文档中提及但后端尚未实现，前端开发时请注意：

- `POST /api/auth/csrf-token` - CSRF Token获取（预留）
- `GET /api/auth/session-info` - 会话详细信息（预留）
- `POST /api/auth/revoke-all-sessions` - 撤销所有会话（预留）

## 7. 开发调试建议

### 7.1 API测试顺序
1. 首先测试健康检查API确保服务可用
2. 测试登录API获取Token
3. 测试需要认证的API端点
4. 测试登出API确保Token撤销

### 7.2 错误日志记录
```typescript
const logApiError = (endpoint: string, error: any) => {
  console.error(`API Error [${endpoint}]:`, {
    message: error.message,
    status: error.status,
    timestamp: new Date().toISOString()
  });
};
```

---

**注意事项**：
1. 确保前端正确实现RSA解密功能
2. 妥善处理Token的生命周期管理
3. 实现适当的错误处理和用户反馈
4. 定期检查会话状态，确保安全性
5. 在生产环境中使用HTTPS确保传输安全