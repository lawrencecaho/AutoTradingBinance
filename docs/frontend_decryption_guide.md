# 前端解密指南

本文档提供了如何在前端正确处理加密响应的指南，特别是针对最近修复的PKCS7填充和base64编码问题。

## 加密响应格式

服务器返回的加密响应可能有三种格式：

1. **标准RSA加密** - 较小数据（<200字节）
2. **混合加密(AES+RSA)** - 中等大小数据（200字节 - 1MB）
3. **分块混合加密** - 大型数据（>1MB）

## Base64编码格式变更

为了解决`atob()`函数解析错误，我们对加密数据进行了以下更改：

1. 使用URL安全的base64格式（替换`+`为`-`，`/`为`_`）
2. 移除填充字符`=`
3. 在响应中添加`base64_format: "url_safe"`标记

## 解密数据的正确步骤

### 1. 解析响应

```javascript
function decryptResponse(encryptedResponse) {
  try {
    // 确保响应是一个对象
    const response = typeof encryptedResponse === 'string' 
      ? JSON.parse(encryptedResponse) 
      : encryptedResponse;
      
    // 检查加密方法
    const encryptionMethod = response.encryption_method;
    
    if (encryptionMethod === 'hybrid') {
      return decryptHybridResponse(response);
    } else if (encryptionMethod === 'chunked_hybrid') {
      return decryptChunkedResponse(response);
    } else {
      // 标准RSA加密或未知方法
      return standardRsaDecrypt(response.data);
    }
  } catch (error) {
    console.error('解密响应失败:', error);
    throw new Error(`无法解密服务器响应: ${error.message}`);
  }
}
```

### 2. 处理URL安全的Base64格式

在解密前，需要将URL安全的base64格式转换回标准格式：

```javascript
function base64UrlToBase64(base64url) {
  // 还原URL安全字符
  let base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  
  // 添加填充
  while (base64.length % 4) {
    base64 += '=';
  }
  
  return base64;
}

function base64ToArrayBuffer(base64) {
  // 处理URL安全的base64格式
  base64 = base64UrlToBase64(base64);
  
  // 转换为二进制数据
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  
  for (let i = 0; i < binaryString.length; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  
  return bytes.buffer;
}
```

### 3. 混合加密解密

```javascript
async function decryptHybridResponse(response) {
  const { encrypted_data, encrypted_key } = response;
  
  if (!encrypted_data || !encrypted_key) {
    throw new Error('加密响应缺少数据或密钥');
  }
  
  // 解密AES密钥
  const keyIv = await decryptWithPrivateKey(encrypted_key);
  
  // 分离AES密钥和IV
  const aesKey = keyIv.slice(0, keyIv.byteLength - 16);
  const iv = keyIv.slice(keyIv.byteLength - 16);
  
  // 使用AES解密数据
  const decryptedData = await decryptAES(encrypted_data, aesKey, iv);
  
  // 解析JSON
  return JSON.parse(decryptedData);
}
```

### 4. PKCS7填充处理

在AES解密后，需要正确移除PKCS7填充：

```javascript
function removePKCS7Padding(data) {
  // 获取填充长度（最后一个字节的值）
  const paddingLength = data[data.length - 1];
  
  // 验证填充长度
  if (paddingLength > 16 || paddingLength > data.length) {
    throw new Error(`异常的PKCS7填充长度: ${paddingLength}`);
  }
  
  // 验证所有填充字节都是相同的值
  for (let i = 1; i <= paddingLength; i++) {
    if (data[data.length - i] !== paddingLength) {
      throw new Error(`无效的PKCS7填充`);
    }
  }
  
  // 移除填充
  return data.slice(0, data.length - paddingLength);
}

async function decryptAES(encryptedBase64, key, iv) {
  try {
    // 将base64转换为ArrayBuffer
    const encryptedData = base64ToArrayBuffer(encryptedBase64);
    
    // 使用Web Crypto API进行AES-CBC解密
    const algorithm = {
      name: 'AES-CBC',
      iv: iv
    };
    
    const cryptoKey = await window.crypto.subtle.importKey(
      'raw', key, algorithm, false, ['decrypt']
    );
    
    const decryptedBuffer = await window.crypto.subtle.decrypt(
      algorithm, cryptoKey, encryptedData
    );
    
    // 转换为Uint8Array以处理PKCS7填充
    const decryptedData = new Uint8Array(decryptedBuffer);
    
    // 移除PKCS7填充
    const unpaddedData = removePKCS7Padding(decryptedData);
    
    // 转换为字符串
    const decoder = new TextDecoder('utf-8');
    return decoder.decode(unpaddedData);
  } catch (error) {
    console.error('AES解密失败:', error);
    throw error;
  }
}
```

### 5. 分块加密解密

对于分块加密的数据，需要单独解密每个块并合并：

```javascript
async function decryptChunkedResponse(response) {
  const { chunks, total_chunks } = response;
  
  if (!chunks || !total_chunks) {
    throw new Error('分块加密响应缺少必要信息');
  }
  
  // 验证块数量
  if (chunks.length !== parseInt(total_chunks, 10)) {
    console.warn(`块数量不匹配: 收到 ${chunks.length}, 期望 ${total_chunks}`);
  }
  
  // 按顺序解密所有块
  const decryptedChunks = [];
  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i];
    
    if (chunk.success === "false") {
      throw new Error(`块 ${chunk.chunk_index} 解密失败: ${chunk.error || '未知错误'}`);
    }
    
    try {
      // 解密单个块
      const { encrypted_data, encrypted_key } = chunk;
      
      // 解密AES密钥
      const keyIv = await decryptWithPrivateKey(encrypted_key);
      
      // 分离AES密钥和IV
      const aesKey = keyIv.slice(0, keyIv.byteLength - 16);
      const iv = keyIv.slice(keyIv.byteLength - 16);
      
      // 使用AES解密数据
      const decryptedData = await decryptAES(encrypted_data, aesKey, iv);
      
      // 添加到结果数组
      decryptedChunks.push(decryptedData);
    } catch (error) {
      console.error(`块 ${chunk.chunk_index} 解密失败:`, error);
      throw error;
    }
  }
  
  // 合并所有块
  const completeData = decryptedChunks.join('');
  
  // 解析JSON
  return JSON.parse(completeData);
}
```

## 错误处理建议

1. 添加详细的日志记录，包括解密过程中的各个步骤
2. 对base64解码错误进行专门处理
3. 对PKCS7填充错误进行明确的错误提示
4. 添加回退机制，在解密失败时可以重试或请求服务器使用其他加密方法

## 测试

建议使用不同大小的数据测试解密功能：

1. 小数据 (<200字节)
2. 中等数据 (200字节 - 1MB)
3. 大数据 (>1MB，使用分块加密)

## 兼容性注意事项

新的加密响应格式使用URL安全的base64编码，这会影响旧版前端的解密功能。请确保更新所有前端代码以兼容新格式。
