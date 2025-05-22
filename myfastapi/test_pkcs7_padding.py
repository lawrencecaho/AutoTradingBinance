#!/usr/bin/env python
"""
PKCS7填充验证测试脚本
测试修复后的分块加密是否正确处理PKCS7填充
"""

import os
import sys
import json
import base64
import logging
from pathlib import Path

# 添加项目根目录到系统路径
sys.path.append(str(Path(__file__).parent.parent))

from myfastapi.chunked_encryption import chunk_encrypt_large_data
from myfastapi.security import hybrid_encrypt_with_client_key
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def generate_test_keypair():
    """生成测试用的RSA密钥对"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    public_key = private_key.public_key()
    
    # 序列化密钥
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem.decode(), public_pem.decode()

def aes_decrypt(encrypted_data_b64, encrypted_key_b64, private_key_pem):
    """使用AES和RSA进行混合解密"""
    try:
        # 确保base64字符串符合标准格式 - 模拟前端处理逻辑
        encrypted_data_b64 = encrypted_data_b64.replace('-', '+').replace('_', '/')
        # 确保长度是4的倍数
        while len(encrypted_data_b64) % 4:
            encrypted_data_b64 += '='
            
        encrypted_key_b64 = encrypted_key_b64.replace('-', '+').replace('_', '/')
        while len(encrypted_key_b64) % 4:
            encrypted_key_b64 += '='
        
        # 解码输入数据
        try:
            encrypted_data = base64.b64decode(encrypted_data_b64)
        except Exception as data_decode_error:
            logger.error(f"解码加密数据失败: {str(data_decode_error)}")
            logger.error(f"问题数据: {encrypted_data_b64[:50]}...")
            raise ValueError(f"无效的base64加密数据: {str(data_decode_error)}")
            
        try:
            encrypted_key = base64.b64decode(encrypted_key_b64)
        except Exception as key_decode_error:
            logger.error(f"解码加密密钥失败: {str(key_decode_error)}")
            logger.error(f"问题数据: {encrypted_key_b64[:50]}...")
            raise ValueError(f"无效的base64加密密钥: {str(key_decode_error)}")
        
        # 加载私钥
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(),
            password=None,
            backend=default_backend()
        )
        
        # 使用RSA私钥解密AES密钥
        padding_algo = padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
        
        key_iv = private_key.decrypt(encrypted_key, padding_algo)
        
        # 分离AES密钥和IV
        aes_key = key_iv[:-16]  # 最后16字节是IV
        iv = key_iv[-16:]
        
        # 使用AES解密数据
        decryptor = Cipher(
            algorithms.AES(aes_key),
            modes.CBC(iv),
            backend=default_backend()
        ).decryptor()
        
        padded_data = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # 处理PKCS7填充
        padding_length = padded_data[-1]
        logger.debug(f"PKCS7填充长度: {padding_length}")
        
        # 验证填充是否有效
        if padding_length > len(padded_data) or padding_length > 16:
            raise ValueError(f"异常的PKCS7填充长度: {padding_length}")
        
        # 验证所有填充字节是否一致
        for i in range(1, padding_length + 1):
            if padded_data[-i] != padding_length:
                raise ValueError(f"无效的PKCS7填充在位置 {-i}: {padded_data[-i]} != {padding_length}")
        
        # 移除填充
        data = padded_data[:-padding_length]
        
        return data.decode()
        
    except Exception as e:
        logger.error(f"解密失败: {str(e)}")
        raise

def test_encryption_decryption_validation():
    """测试加密和解密，验证PKCS7填充处理"""
    print("开始PKCS7填充验证测试...")
    
    # 生成测试密钥
    private_key, public_key = generate_test_keypair()
    
    # 模拟前端环境中的解密过程
    def simulate_frontend_decryption(encrypted_response):
        print("\n模拟前端解密过程:")
        
        # 1. 转换为字符串，模拟网络传输
        response_str = json.dumps(encrypted_response)
        
        # 2. 解析JSON
        try:
            parsed_response = json.loads(response_str)
        except json.JSONDecodeError as json_error:
            print(f"❌ JSON解析失败: {str(json_error)}")
            return None
            
        # 3. 根据加密方法执行不同的解密逻辑
        if parsed_response.get("encryption_method") == "hybrid":
            # 标准混合加密
            print("检测到标准混合加密格式")
            
            encrypted_data = parsed_response.get("encrypted_data")
            encrypted_key = parsed_response.get("encrypted_key")
            
            if not encrypted_data or not encrypted_key:
                print("❌ 缺少加密数据或密钥")
                return None
                
            try:
                # 模拟前端解密
                decrypted_data = aes_decrypt(encrypted_data, encrypted_key, private_key)
                print(f"✅ 前端解密成功! 长度: {len(decrypted_data)} 字节")
                return decrypted_data
            except Exception as decrypt_error:
                print(f"❌ 前端解密失败: {str(decrypt_error)}")
                return None
                
        elif parsed_response.get("encryption_method") == "chunked_hybrid":
            # 分块混合加密
            print("检测到分块混合加密格式")
            
            chunks = parsed_response.get("chunks", [])
            if not chunks:
                print("❌ 没有找到加密数据块")
                return None
                
            # 解密第一个块作为示例
            first_chunk = chunks[0]
            encrypted_data = first_chunk.get("encrypted_data")
            encrypted_key = first_chunk.get("encrypted_key")
            
            if not encrypted_data or not encrypted_key:
                print("❌ 第一个块缺少加密数据或密钥")
                return None
                
            try:
                # 模拟前端解密
                decrypted_chunk = aes_decrypt(encrypted_data, encrypted_key, private_key)
                print(f"✅ 前端解密第一个块成功! 长度: {len(decrypted_chunk)} 字节")
                return decrypted_chunk
            except Exception as chunk_error:
                print(f"❌ 前端解密第一个块失败: {str(chunk_error)}")
                return None
        else:
            print(f"❌ 未知的加密方法: {parsed_response.get('encryption_method')}")
            return None
    
    # 测试不同大小的数据
    test_data_sizes = [
        ("小数据", "这是一个小型测试数据字符串。" * 2),  # 约60字节
        ("中等数据", "这是一个中等大小的测试数据。" * 100),  # 约3000字节
        ("大数据", "这是一个较大的测试数据字符串，测试分块加密功能。" * 1000)  # 约30000字节
    ]
    
    for name, test_data in test_data_sizes:
        print(f"\n测试 {name} (长度: {len(test_data)} 字节):")
        
        # 1. 加密数据
        if len(test_data) > 1024 * 10:  # 大于10KB使用分块加密
            print("使用分块加密...")
            encrypted_result = chunk_encrypt_large_data(test_data, public_key, chunk_size=1024*10)
            print(f"加密结果类型: {encrypted_result['encryption_method']}")
            
            # 打印第一个块的信息用于调试
            if "chunks" in encrypted_result and len(encrypted_result["chunks"]) > 0:
                first_chunk = encrypted_result["chunks"][0]
                print(f"第一个块信息: 索引={first_chunk.get('chunk_index')}, 总块数={first_chunk.get('total_chunks')}")
                print(f"PKCS7填充验证: {first_chunk.get('padding_verified', '未知')}")
                
                # 验证模拟前端解密
                frontend_decrypted = simulate_frontend_decryption(encrypted_result)
                if frontend_decrypted:
                    print(f"解密数据预览: {frontend_decrypted[:50]}...")
                
                # 直接解密验证
                try:
                    decrypted_data = aes_decrypt(
                        first_chunk["encrypted_data"],
                        first_chunk["encrypted_key"],
                        private_key
                    )
                    print(f"第一个块解密成功! 解密数据长度: {len(decrypted_data)} 字节")
                    print(f"解密数据预览: {decrypted_data[:50]}...")
                except Exception as e:
                    print(f"第一个块解密失败: {str(e)}")
        else:
            # 使用标准混合加密
            print("使用标准混合加密...")
            encrypted_result = hybrid_encrypt_with_client_key(test_data, public_key)
            print(f"加密结果类型: {encrypted_result['encryption_method']}")
            
            # 验证模拟前端解密
            frontend_decrypted = simulate_frontend_decryption(encrypted_result)
            if frontend_decrypted:
                print(f"解密数据预览: {frontend_decrypted[:50]}...")
                
                # 验证数据一致性
                if frontend_decrypted == test_data:
                    print("✅ 原始数据和解密数据完全匹配!")
                else:
                    print("❌ 解密数据与原始数据不匹配!")
            
            # 解密并验证
            try:
                decrypted_data = aes_decrypt(
                    encrypted_result["encrypted_data"],
                    encrypted_result["encrypted_key"],
                    private_key
                )
                print(f"解密成功! 解密数据长度: {len(decrypted_data)} 字节")
                print(f"解密数据预览: {decrypted_data[:50]}...")
                
                # 验证数据一致性
                if decrypted_data == test_data:
                    print("✅ 原始数据和解密数据完全匹配!")
                else:
                    print("❌ 解密数据与原始数据不匹配!")
            except Exception as e:
                print(f"解密失败: {str(e)}")

if __name__ == "__main__":
    test_encryption_decryption_validation()
