# 响应加密文档（更新版）

## 概述

本系统实现了完整的双向加密通信，不仅请求数据被加密，响应数据也经过加密，确保前后端通信的端到端安全。最新版本添加了混合加密支持，解决了RSA加密的大小限制问题。

## 关键组件

1. **客户端公钥注册**：前端生成RSA密钥对，并向后端注册公钥
2. **混合加密支持**：当响应数据较大时，系统自动切换到AES+RSA混合加密
3. **响应加密**：后端使用客户端公钥加密响应数据
4. **响应解密**：前端使用自己的私钥解密从服务器接收的数据

## 流程说明

### 1. 初始化阶段

1. 前端生成RSA密钥对（公钥和私钥）
2. 前端向后端发送自己的公钥
3. 后端存储客户端公钥，与客户端ID关联

### 2. 加密通信阶段

1. 前端发送加密请求到后端（使用后端公钥加密）
2. 后端解密请求并处理
3. 后端准备响应数据
4. 后端检查响应数据大小：
   - 如果小于200字节：使用客户端公钥直接加密（RSA加密）
   - 如果大于200字节：使用混合加密（AES+RSA）
5. 后端发送加密响应到前端
6. 前端使用自己的私钥解密响应

## 混合加密详解

当响应数据超过RSA加密的大小限制（约200字节）时，系统会自动使用混合加密：

1. 生成随机AES密钥和初始化向量（IV）
2. 使用AES加密响应数据
3. 使用客户端RSA公钥加密AES密钥和IV
4. 将加密数据和加密密钥一起发送给客户端
5. 客户端使用私钥解密AES密钥，然后使用AES密钥解密数据

更详细的混合加密实现可参考 [混合加密实现指南](./hybrid_encryption.md)。

## 代码示例

### 后端加密响应

```python
def encrypt_response(response_data: Dict[str, Any], client_id: Optional[str] = None):
    client_public_key = get_client_public_key(client_id)
    
    if client_public_key:
        if len(json_data) > 200:  # 大数据使用混合加密
            hybrid_result = hybrid_encrypt_with_client_key(json_data, client_public_key)
            encrypted_data = json.dumps(hybrid_result)
        else:  # 小数据直接RSA加密
            encrypted_data = encrypt_with_client_key(json_data, client_public_key)
    else:
        encrypted_data = encrypt_data(json_data)  # 回退到标准加密
```

### 前端解密响应

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
        // 继续使用标准RSA解密
    }
    
    // 标准RSA解密过程
    const decryptedBuffer = await crypto.subtle.decrypt(
        { name: 'RSA-OAEP' },
        privateKey,
        base64ToArrayBuffer(encryptedData)
    );
    
    return JSON.parse(new TextDecoder().decode(decryptedBuffer));
}
```

## 安全考虑

1. **前端密钥安全**：前端生成的私钥仅存储在内存中，不持久化存储
2. **会话隔离**：每个客户端有独立的密钥对，确保会话隔离
3. **大数据加密**：混合加密机制确保任意大小的数据都能安全传输
4. **密钥轮换**：建议客户端定期重新生成密钥对并重新注册

## 测试

使用 `test_response_encryption.py` 测试响应加密功能：

```bash
python myfastapi/test_response_encryption.py
```
