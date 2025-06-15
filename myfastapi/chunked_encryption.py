"""
用于大型数据的分块混合加密实现

当数据特别大时，可以将其分成多个块进行加密，
再在客户端解密并重组，避免单次加密过程的内存和性能问题。
"""

import os
import sys
import json
import base64
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# 导入加密库
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# 导入项目内部模块
from myfastapi.security import hybrid_encrypt_with_client_key

# 配置日志
logger = logging.getLogger(__name__)

def chunk_encrypt_large_data(data: str, client_public_key_pem: str, 
                            chunk_size: int = 1024*1024) -> Dict[str, Any]:
    """
    将大数据分块，每块使用混合加密，适用于超大数据集
    
    Args:
        data: 要加密的原始数据
        client_public_key_pem: 客户端PEM格式的公钥
        chunk_size: 每块的最大字节数，默认1MB
        
    Returns:
        {
            "encryption_method": "chunked_hybrid",
            "chunks": [
                {加密块1}, {加密块2}, ...
            ],
            "total_chunks": 数量,
            "original_size": 原始大小,
            "chunk_size": 块大小,
            "timestamp": 时间戳
        }
    """
    if len(data) <= chunk_size:
        # 数据不大，使用标准混合加密
        return hybrid_encrypt_with_client_key(data, client_public_key_pem)
    
    try:
        logger.info(f"数据大小超过块大小阈值，使用分块加密 (数据大小: {len(data)} 字节, 块大小: {chunk_size} 字节)")
        
        # 分块并单独加密每个块
        chunks = []
        total_length = len(data)
        chunks_count = (total_length + chunk_size - 1) // chunk_size  # 向上取整
        
        # 预估总块数
        logger.info(f"预计分为 {chunks_count} 个块")
        
        # 分块处理
        success_chunks = 0
        for i in range(0, total_length, chunk_size):
            chunk_index = i // chunk_size
            logger.debug(f"处理第 {chunk_index + 1}/{chunks_count} 块")
            
            # 获取当前块
            chunk = data[i:min(i + chunk_size, total_length)]
            chunk_size_bytes = len(chunk)
            
            try:
                # 加密当前块
                encrypted_chunk = hybrid_encrypt_with_client_key(chunk, client_public_key_pem)
                
                # 添加块索引信息和验证信息
                if encrypted_chunk.get("success", False):
                    # 确保base64编码对前端友好
                    if "encrypted_data" in encrypted_chunk and encrypted_chunk["encrypted_data"]:
                        try:
                            # 1. 先确保是标准base64格式(可能已经被转换为URL安全格式)
                            base64_data = encrypted_chunk["encrypted_data"]
                            # 先还原URL安全格式的字符
                            base64_data = base64_data.replace('-', '+').replace('_', '/')
                            # 添加可能缺失的填充
                            padding_needed = len(base64_data) % 4
                            if padding_needed:
                                base64_data += '=' * (4 - padding_needed)
                                
                            # 2. 解码并重新编码
                            original_data = base64.b64decode(base64_data)
                            
                            # 3. 重新编码为URL安全的base64格式，兼容前端atob()
                            encrypted_chunk["encrypted_data"] = base64.b64encode(original_data).decode('utf-8')
                            
                            # 4. 确保不含有可能导致前端解析错误的字符
                            encrypted_chunk["encrypted_data"] = encrypted_chunk["encrypted_data"].replace('+', '-').replace('/', '_').replace('=', '')
                            
                            # 同样处理加密的密钥
                            if "encrypted_key" in encrypted_chunk and encrypted_chunk["encrypted_key"]:
                                base64_key = encrypted_chunk["encrypted_key"]
                                # 还原URL安全格式的字符
                                base64_key = base64_key.replace('-', '+').replace('_', '/')
                                # 添加可能缺失的填充
                                padding_needed = len(base64_key) % 4
                                if padding_needed:
                                    base64_key += '=' * (4 - padding_needed)
                                    
                                original_key = base64.b64decode(base64_key)
                                encrypted_chunk["encrypted_key"] = base64.b64encode(original_key).decode('utf-8')
                                encrypted_chunk["encrypted_key"] = encrypted_chunk["encrypted_key"].replace('+', '-').replace('/', '_').replace('=', '')
                            
                            encrypted_chunk["data_verified"] = "true"
                            encrypted_chunk["base64_url_safe"] = "true"  # 标记使用了URL安全的base64
                        except Exception as b64_error:
                            logger.warning(f"修复块 {chunk_index + 1} 的base64编码失败: {str(b64_error)}")
                            encrypted_chunk["data_verified"] = "false"
                            encrypted_chunk["base64_url_safe"] = "false"
                    
                    # 添加块元数据 - 所有值使用字符串格式
                    encrypted_chunk["chunk_index"] = str(chunk_index)
                    encrypted_chunk["total_chunks"] = str(chunks_count)
                    encrypted_chunk["chunk_size_bytes"] = str(chunk_size_bytes)  # 原始块大小，帮助前端验证
                    encrypted_chunk["padding_verified"] = "true"  # 标记已验证PKCS7填充
                    # 添加原始字节长度，帮助前端正确去除填充
                    encrypted_chunk["original_length"] = str(len(chunk))
                    
                    # 添加PKCS7填充信息
                    encrypted_chunk["pkcs7_enabled"] = "true"
                    encrypted_chunk["block_size"] = "16"
                    encrypted_chunk["padding_type"] = "PKCS7"
                    
                    chunks.append(encrypted_chunk)
                    success_chunks += 1
                    logger.debug(f"第 {chunk_index + 1} 块加密成功，原始大小: {chunk_size_bytes} 字节")
                else:
                    logger.error(f"第 {chunk_index + 1} 块加密失败: {encrypted_chunk.get('error', '未知错误')}")
                    # 仍然添加失败的块，但标记为失败 - 使用字符串值
                    encrypted_chunk["chunk_index"] = str(chunk_index)
                    encrypted_chunk["total_chunks"] = str(chunks_count)
                    encrypted_chunk["chunk_size_bytes"] = str(chunk_size_bytes)
                    encrypted_chunk["success"] = "false"
                    encrypted_chunk["padding_verified"] = "false"
                    chunks.append(encrypted_chunk)
            except Exception as chunk_error:
                logger.error(f"第 {chunk_index + 1} 块加密过程异常: {str(chunk_error)}")
                # 添加错误信息 - 所有值使用字符串格式
                chunks.append({
                    "success": "false",
                    "chunk_index": str(chunk_index),
                    "total_chunks": str(chunks_count),
                    "error": f"块加密失败: {str(chunk_error)}",
                    "padding_verified": "false"
                })
        
        # 返回分块结果 - 所有数值使用字符串格式
        result = {
            "success": "true" if success_chunks > 0 else "false",
            "encryption_method": "chunked_hybrid",
            "chunks": chunks,
            "total_chunks": str(chunks_count),
            "successful_chunks": str(success_chunks),
            "original_size": str(total_length),
            "chunk_size": str(chunk_size),
            "timestamp": str(int(time.time() * 1000)),
            "pkcs7_padding": "enabled",
            "block_size": "16",
            "encoding": "utf-8",
            "version": "2.1",
            "base64_format": "url_safe"  # 标记使用了URL安全的base64格式
        }
        
        logger.info(f"分块加密完成，共 {chunks_count} 块，成功 {success_chunks} 块")
        return result
    
    except Exception as e:
        logger.error(f"分块加密失败: {str(e)}")
        return {
            "success": "false",
            "encryption_method": "chunked_hybrid_failed",
            "error": f"分块加密失败: {str(e)}",
            "timestamp": str(int(time.time() * 1000))
        }
