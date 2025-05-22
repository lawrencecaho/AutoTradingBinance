<!-- 
本文档详细描述了混合加密系统（AES+RSA）的边界情况处理和错误恢复机制，
以确保大型数据响应的加密处理更加稳健。
-->

# 混合加密边界情况处理

## 潜在问题

在混合加密（AES+RSA）实现中，可能出现以下边界情况：

1. **密钥长度问题**：RSA加密AES密钥时可能发生溢出
2. **格式错误**：JSON解析失败或格式不符合预期
3. **网络问题**：部分数据丢失导致解密失败
4. **AES填充问题**：PKCS7填充可能导致不一致
5. **密钥兼容性**：前端WebCrypto API与后端cryptography库可能有差异

## 改进建议

### 1. 增强前端错误处理

```typescript
export async function decryptResponse(encryptedData: string, privateKey: CryptoKey): Promise<any> {
  try {
    // 首先尝试解析为JSON，检查是否是混合加密格式
    try {
      const parsedData = JSON.parse(encryptedData);
      
      // 添加更严格的格式验证
      if (parsedData.encrypted_data && parsedData.encrypted_key && parsedData.encryption_method === 'hybrid') {
        try {
          return await decryptHybridResponse(parsedData, privateKey);
        } catch (hybridError) {
          console.error('混合加密解密失败，尝试标准解密:', hybridError);
          // 如果混合解密失败，尝试作为普通字符串进行标准RSA解密
          return await standardDecrypt(encryptedData, privateKey);
        }
      }
    } catch (parseError) {
      // 不是JSON格式，继续使用标准RSA解密
    }
    
    // 标准RSA解密
    return await standardDecrypt(encryptedData, privateKey);
  } catch (error) {
    // 所有解密方法都失败，提供清晰的错误信息
    console.error('所有解密方法均失败:', error);
    throw new Error(`解密失败: ${error instanceof Error ? error.message : String(error)}`);
  }
}

// 提取标准RSA解密为单独函数，便于错误处理和代码复用
async function standardDecrypt(encryptedData: string, privateKey: CryptoKey): Promise<any> {
  try {
    const encryptedBuffer = base64ToArrayBuffer(encryptedData);
    const decryptedBuffer = await crypto.subtle.decrypt(
      { name: 'RSA-OAEP' },
      privateKey,
      encryptedBuffer
    );
    
    const decoder = new TextDecoder();
    const decryptedText = decoder.decode(decryptedBuffer);
    return JSON.parse(decryptedText);
  } catch (error) {
    console.error('标准RSA解密失败:', error);
    throw error;
  }
}
```

### 2. 增强后端混合加密错误处理

```python
def hybrid_encrypt_with_client_key(data: str, client_public_key_pem: str) -> Dict[str, str]:
    """使用混合加密（AES+RSA）加密大型数据"""
    try:
        # [原有代码...]
        
        # 1. 生成随机AES密钥和初始化向量
        aes_key = os.urandom(32)  # 256位密钥
        iv = os.urandom(16)       # 128位IV
        
        # 检查客户端公钥能否加密48字节(密钥+IV)
        key_size_bytes = (client_public_key.key_size + 7) // 8
        max_key_plaintext_size = key_size_bytes - 42  # OAEP填充
        if max_key_plaintext_size < 48:
            logger.warning("客户端RSA密钥太小，无法安全加密AES密钥和IV")
            # 降级为较小的AES密钥 (如果确实需要)
            aes_key = os.urandom(16)  # 降级到128位AES密钥
            
        # 2. 使用AES加密数据，添加更多错误处理
        try:
            # [AES加密代码...]
        except Exception as aes_error:
            logger.error(f"AES加密失败: {str(aes_error)}")
            raise ValueError(f"AES加密失败: {str(aes_error)}")
            
        # 3. 使用RSA加密AES密钥，添加更多错误处理
        try:
            # [RSA加密代码...]
        except Exception as rsa_error:
            logger.error(f"RSA加密AES密钥失败: {str(rsa_error)}")
            raise ValueError(f"RSA加密AES密钥失败: {str(rsa_error)}")
            
        # 4. 返回加密结果，添加额外的元数据
        return {
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "encrypted_key": base64.b64encode(encrypted_key).decode(),
            "encryption_method": "hybrid",
            "aes_key_size": len(aes_key) * 8,  # 添加密钥大小信息
            "aes_mode": "CBC",                 # 添加模式信息
            "timestamp": int(time.time() * 1000)  # 添加时间戳
        }
            
    except Exception as e:
        logger.error(f"混合加密失败: {str(e)}")
        # 返回明确的错误代码和消息，而不是抛出通用HTTP异常
        raise ValueError(f"混合加密失败: {str(e)}")
```

### 3. 增强主加密逻辑中的错误恢复

```python
def encrypt_response(response_data: Dict[str, Any], client_id: Optional[str] = None) -> EncryptedResponse:
    """加密响应数据并生成签名"""
    current_timestamp = int(time.time() * 1000)
    
    try:
        json_data = json.dumps(response_data)
        data_size = len(json_data)
        logger.debug(f"原始响应数据大小: {data_size} 字节")
        
        # 提前分析数据大小，确定加密策略
        encryption_strategy = "standard"
        if data_size > 200:
            encryption_strategy = "hybrid"
            logger.debug(f"选择混合加密策略 (数据大小: {data_size} 字节)")
        else:
            logger.debug(f"选择标准加密策略 (数据大小: {data_size} 字节)")
        
        # 尝试多种加密方法，有优先级
        encrypted_data = None
        encryption_methods_tried = []
        
        # 1. 尝试使用客户端公钥进行加密
        if client_id:
            client_public_key = get_client_public_key(client_id)
            if client_public_key:
                try:
                    if encryption_strategy == "hybrid":
                        # 尝试混合加密
                        hybrid_result = hybrid_encrypt_with_client_key(json_data, client_public_key)
                        encrypted_data = json.dumps(hybrid_result)
                        encryption_methods_tried.append("hybrid")
                    else:
                        # 尝试标准RSA加密
                        encrypted_data = encrypt_with_client_key(json_data, client_public_key)
                        encryption_methods_tried.append("client_rsa")
                except Exception as client_encrypt_error:
                    logger.warning(f"客户端加密失败: {str(client_encrypt_error)}")
                    # 继续尝试下一种加密方法
        
        # 2. 如果客户端加密失败，使用服务器加密
        if encrypted_data is None:
            try:
                encrypted_data = encrypt_data(json_data)
                encryption_methods_tried.append("server_rsa")
            except Exception as server_encrypt_error:
                logger.error(f"服务器加密失败: {str(server_encrypt_error)}")
                # 如果所有加密方法都失败，使用明文JSON并添加错误标记
                encrypted_data = json.dumps({
                    "error": "encryption_failed",
                    "message": "无法加密响应数据，请联系管理员",
                    "timestamp": current_timestamp
                })
                encryption_methods_tried.append("plaintext_fallback")
        
        # 记录最终使用的加密方法
        logger.info(f"响应加密完成，使用方法: {', '.join(encryption_methods_tried)}")
        
        # 生成签名
        signature = sign_data(encrypted_data, str(current_timestamp))
        
        return EncryptedResponse(
            data=encrypted_data,
            timestamp=current_timestamp,
            signature=signature
        )
    except Exception as e:
        logger.error(f"加密响应过程中发生意外错误: {str(e)}")
        # 最终的错误处理，确保总是返回某种响应
        try:
            error_data = json.dumps({"error": "unexpected_error", "message": str(e)})
            signature = sign_data(error_data, str(current_timestamp))
            return EncryptedResponse(
                data=error_data,
                timestamp=current_timestamp,
                signature=signature
            )
        except:
            # 即使签名失败，也返回某种响应
            return EncryptedResponse(
                data=json.dumps({"error": "critical_failure"}),
                timestamp=current_timestamp,
                signature="error"
            )
```

## 数据分块考虑

对于特别大的数据集，可以考虑实现分块传输：

```python
def chunk_encrypt_large_data(data: str, client_public_key_pem: str, 
                            chunk_size: int = 1024*1024) -> Dict[str, Any]:
    """
    将大数据分块，每块使用混合加密，适用于超大数据集
    
    返回:
    {
        "encryption_method": "chunked_hybrid",
        "chunks": [
            {加密块1}, {加密块2}, ...
        ],
        "total_chunks": 数量,
        "original_size": 原始大小
    }
    """
    if len(data) <= chunk_size:
        # 数据不大，使用标准混合加密
        return hybrid_encrypt_with_client_key(data, client_public_key_pem)
        
    # 分块并单独加密每个块
    chunks = []
    total_length = len(data)
    for i in range(0, total_length, chunk_size):
        chunk = data[i:i+chunk_size]
        encrypted_chunk = hybrid_encrypt_with_client_key(chunk, client_public_key_pem)
        chunks.append(encrypted_chunk)
    
    # 返回分块结果
    return {
        "encryption_method": "chunked_hybrid",
        "chunks": chunks,
        "total_chunks": len(chunks),
        "original_size": total_length
    }
```

前端对应实现:

```typescript
async function decryptChunkedResponse(chunkedData: any, privateKey: CryptoKey): Promise<any> {
    if (chunkedData.encryption_method !== 'chunked_hybrid') {
        throw new Error('不是分块加密格式');
    }
    
    // 解密每个块
    const decryptedChunks: string[] = [];
    for (const chunk of chunkedData.chunks) {
        const decryptedChunk = await decryptHybridResponse(chunk, privateKey);
        decryptedChunks.push(decryptedChunk);
    }
    
    // 合并解密后的数据
    const fullData = decryptedChunks.join('');
    
    // 解析为JSON
    return JSON.parse(fullData);
}
```

## 最佳实践总结

1. **异常处理层次化**：从具体到一般，确保每层都有适当的错误处理
2. **多重加密策略**：基于数据大小和场景自动选择最合适的加密方法
3. **错误恢复机制**：即使加密失败也能返回有意义的响应
4. **详细日志记录**：记录每一步的加密策略选择和错误情况
5. **元数据丰富**：在加密结果中包含足够的元数据，帮助接收方正确解密
6. **安全降级**：在必要时使用安全的降级策略，确保系统可用性
7. **持续监控**：监控加密/解密错误率，发现潜在问题
