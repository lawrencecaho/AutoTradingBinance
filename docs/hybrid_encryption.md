# 混合加密实现指南

## 背景

在RSA加密中，明文数据的大小限制由密钥大小决定。使用2048位RSA密钥和OAEP填充时，最大可加密的数据大小约为214字节。当需要加密较大的数据时，直接使用RSA加密会失败。

## 解决方案：混合加密

混合加密结合了对称加密(AES)和非对称加密(RSA)的优势:
1. 使用AES加密大型数据 - AES可以加密任意大小的数据，且速度快
2. 使用RSA加密AES密钥 - RSA用于安全传输AES密钥

## 后端实现

### 1. 混合加密函数 (security.py)

```python
def hybrid_encrypt_with_client_key(data: str, client_public_key_pem: str) -> Dict[str, str]:
    # 1. 生成随机AES密钥和初始化向量
    aes_key = os.urandom(32)  # 256位密钥
    iv = os.urandom(16)       # 128位IV
    
    # 2. 使用AES加密数据
    data_bytes = data.encode()
    # [AES加密实现]
    
    # 3. 使用客户端RSA公钥加密AES密钥
    # [RSA加密实现]
    
    # 4. 返回混合加密结果
    return {
        "encrypted_data": base64.b64encode(encrypted_data).decode(),
        "encrypted_key": base64.b64encode(encrypted_key).decode(),
        "encryption_method": "hybrid"
    }
```

### 2. 响应加密逻辑 (main.py)

```python
def encrypt_response(response_data: Dict[str, Any], client_id: Optional[str] = None):
    # 判断数据大小
    if len(json_data) > 200:  # 超过RSA限制
        # 使用混合加密
        hybrid_result = hybrid_encrypt_with_client_key(json_data, client_public_key)
        encrypted_data = json.dumps(hybrid_result)
    else:
        # 直接使用RSA加密
        encrypted_data = encrypt_with_client_key(json_data, client_public_key)
```

## 前端实现

### 1. 解密响应 (decryptResponse.ts)

```typescript
export async function decryptResponse(encryptedData: string, privateKey: CryptoKey): Promise<any> {
    // 检查是否是混合加密格式
    try {
        const parsedData = JSON.parse(encryptedData);
        if (parsedData.encryption_method === 'hybrid') {
            // 处理混合加密
            return await decryptHybridResponse(parsedData, privateKey);
        }
    } catch (parseError) {
        // 不是JSON格式，继续使用标准RSA解密
    }
    
    // 标准RSA解密
    // [RSA解密实现]
}
```

### 2. 混合加密解密 (decryptResponse.ts)

```typescript
async function decryptHybridResponse(hybridData, privateKey): Promise<any> {
    // 1. 使用RSA私钥解密AES密钥
    // [RSA解密实现]
    
    // 2. 分离AES密钥和IV
    // [分离密钥和IV]
    
    // 3. 使用AES解密数据
    // [AES解密实现]
    
    // 4. 返回解密结果
    // [返回JSON解析结果]
}
```

## 数据流程

1. 后端生成JSON响应
2. 检查响应大小:
   - 如果小于200字节：直接RSA加密
   - 如果大于200字节：使用混合加密(AES+RSA)
3. 发送加密响应到前端
4. 前端检查响应格式:
   - 如果是混合加密格式：先RSA解密AES密钥，再用AES解密数据
   - 如果是标准格式：直接用RSA解密

## 错误处理

- 如果混合加密失败，后端会回退到标准加密
- 前端会先尝试解析为混合格式，如果失败再尝试标准解密
- 完整的错误日志记录在后端和前端

## 安全注意事项

- AES密钥和IV是随机生成的，每次请求都不同
- 使用CBC模式的AES加密提供更高的安全性
- 同时传输AES密钥和IV，使用RSA进行保护
