"""
测试分块加密功能

此脚本用于测试大型数据的分块加密，验证加密和解密过程的正确性
"""

import os
import json
import base64
import time
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
except ImportError:
    logger.error("未安装cryptography库，请使用 pip install cryptography 安装")
    sys.exit(1)

# 导入项目模块
from myfastapi.chunked_encryption import chunk_encrypt_large_data
from myfastapi.test_hybrid_encryption import generate_key_pair, hybrid_decrypt

def decrypt_chunked_data(chunked_data: Dict[str, Any], private_key) -> str:
    """
    解密分块加密的数据
    
    Args:
        chunked_data: 分块加密结果字典
        private_key: RSA私钥对象
        
    Returns:
        解密后的原始数据
    """
    logger.info("解密分块加密数据")
    
    # 如果不是分块加密，则当作标准混合加密处理
    if chunked_data.get("encryption_method") != "chunked_hybrid":
        logger.info("不是分块加密格式，尝试作为标准混合加密处理")
        return hybrid_decrypt(chunked_data, private_key)
    
    # 检查必要字段
    if "chunks" not in chunked_data or "total_chunks" not in chunked_data:
        raise ValueError("无效的分块加密数据格式，缺少必要字段")
    
    # 获取块数量
    total_chunks = chunked_data["total_chunks"]
    received_chunks = len(chunked_data["chunks"])
    
    logger.info(f"开始解密分块数据: 共{total_chunks}块，接收{received_chunks}块")
    
    # 检查是否收到所有块
    if received_chunks < total_chunks:
        logger.warning(f"未收到所有块: {received_chunks}/{total_chunks}")
    
    # 对块进行排序
    sorted_chunks = sorted(chunked_data["chunks"], key=lambda x: x.get("chunk_index", 0))
    
    # 解密每个块
    decrypted_chunks = []
    for i, chunk in enumerate(sorted_chunks):
        try:
            if not chunk.get("success", True):
                logger.error(f"块 {i} 标记为加密失败，无法解密")
                raise ValueError(f"块 {i} 加密失败: {chunk.get('error', '未知错误')}")
            
            logger.info(f"解密块 {i+1}/{len(sorted_chunks)}")
            decrypted_chunk = hybrid_decrypt(chunk, private_key)
            decrypted_chunks.append(decrypted_chunk)
            logger.info(f"块 {i+1} 解密成功，长度: {len(decrypted_chunk)}字节")
        except Exception as e:
            logger.error(f"解密块 {i+1} 失败: {str(e)}")
            raise ValueError(f"解密块 {i+1} 失败: {str(e)}")
    
    # 合并解密后的块
    combined_data = "".join(decrypted_chunks)
    logger.info(f"所有块解密完成，合并后大小: {len(combined_data)}字节")
    
    return combined_data

def generate_test_data(size_kb: int) -> str:
    """生成指定大小的测试数据"""
    logger.info(f"生成 {size_kb}KB 的测试数据")
    
    # 创建包含不同字符的测试数据，防止简单重复造成压缩
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    data_length = size_kb * 1024
    
    # 创建一个固定模式的数据，使其不易压缩
    parts = []
    part_size = min(1024, data_length)
    
    for i in range(0, data_length, part_size):
        # 以不同的种子创建数据块
        seed = (i // part_size) % 100
        part = "".join(chars[(j + seed) % len(chars)] for j in range(min(part_size, data_length - i)))
        parts.append(part)
    
    test_data = "".join(parts)
    
    # 验证大小
    actual_size = len(test_data)
    logger.info(f"生成的测试数据大小: {actual_size} 字节")
    
    return test_data

def run_chunked_encryption_test(data_size_kb: int = 1024, chunk_size_kb: int = 64, key_size: int = 2048):
    """
    运行分块加密测试
    
    Args:
        data_size_kb: 测试数据大小，单位KB
        chunk_size_kb: 分块大小，单位KB
        key_size: RSA密钥大小，单位位
    """
    logger.info(f"====== 开始分块加密测试 (数据大小: {data_size_kb} KB, 块大小: {chunk_size_kb} KB, RSA密钥: {key_size} 位) ======")
    
    # 生成测试数据
    test_data = generate_test_data(data_size_kb)
    
    # 生成密钥对
    public_pem, private_pem, private_key = generate_key_pair(key_size)
    
    # 测量开始时间
    start_time = time.time()
    
    # 加密
    encrypted = chunk_encrypt_large_data(
        test_data, 
        public_pem, 
        chunk_size=chunk_size_kb * 1024
    )
    
    # 计算加密时间
    encryption_time = time.time() - start_time
    
    if not encrypted.get("success", False):
        logger.error(f"分块加密测试失败: {encrypted.get('error', '未知错误')}")
        return False
    
    # 记录中间信息
    total_chunks = encrypted.get("total_chunks", 0)
    successful_chunks = encrypted.get("successful_chunks", 0)
    
    logger.info(f"加密完成: 用时 {encryption_time:.2f}秒, 成功 {successful_chunks}/{total_chunks} 块")
    
    # 重置计时
    start_time = time.time()
    
    # 解密
    try:
        decrypted = decrypt_chunked_data(encrypted, private_key)
        
        # 计算解密时间
        decryption_time = time.time() - start_time
        logger.info(f"解密完成: 用时 {decryption_time:.2f}秒")
        
        # 验证
        if decrypted == test_data:
            logger.info("分块加密测试成功: 解密后数据与原始数据匹配")
            
            # 统计信息
            original_size = len(test_data)
            encrypted_size = sum(len(json.dumps(chunk)) for chunk in encrypted["chunks"])
            
            logger.info(f"性能统计:")
            logger.info(f"  - 原始数据大小: {original_size/1024:.2f} KB")
            logger.info(f"  - 加密后大小: {encrypted_size/1024:.2f} KB")
            logger.info(f"  - 膨胀率: {encrypted_size/original_size:.2f}x")
            logger.info(f"  - 加密速度: {original_size/1024/encryption_time:.2f} KB/s")
            logger.info(f"  - 解密速度: {original_size/1024/decryption_time:.2f} KB/s")
            
            return True
        else:
            logger.error(f"分块加密测试失败: 解密后数据与原始数据不匹配 (原始长度: {len(test_data)}, 解密后长度: {len(decrypted)})")
            return False
    except Exception as e:
        logger.error(f"分块加密测试解密阶段失败: {str(e)}")
        return False

def test_different_sizes():
    """测试不同大小的数据"""
    logger.info("\n====== 不同数据大小测试 ======")
    
    test_cases = [
        {"name": "100 KB", "size_kb": 100, "chunk_kb": 50, "expected_success": True},
        {"name": "500 KB", "size_kb": 500, "chunk_kb": 100, "expected_success": True},
        {"name": "2 MB", "size_kb": 2048, "chunk_kb": 256, "expected_success": True},
        {"name": "5 MB", "size_kb": 5120, "chunk_kb": 512, "expected_success": True},
    ]
    
    results = []
    
    for case in test_cases:
        logger.info(f"\n测试案例: {case['name']}")
        try:
            success = run_chunked_encryption_test(
                data_size_kb=case["size_kb"],
                chunk_size_kb=case["chunk_kb"]
            )
            
            if success == case["expected_success"]:
                logger.info(f"✅ 测试案例 '{case['name']}' 通过")
                results.append(True)
            else:
                logger.error(f"❌ 测试案例 '{case['name']}' 失败: 期望 {case['expected_success']} 但得到 {success}")
                results.append(False)
        except Exception as e:
            logger.error(f"❌ 测试案例 '{case['name']}' 失败，发生异常: {str(e)}")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    logger.info(f"\n不同数据大小测试完成: 通过率 {success_rate:.2f}% ({sum(results)}/{len(results)})")
    return all(results)

if __name__ == "__main__":
    logger.info("开始分块加密测试")
    
    # 单一测试
    single_test_success = run_chunked_encryption_test(
        data_size_kb=512,  # 0.5MB
        chunk_size_kb=128  # 128KB每块
    )
    
    # 不同大小测试
    multiple_sizes_test = test_different_sizes()
    
    # 汇总结果
    if single_test_success and multiple_sizes_test:
        logger.info("\n🎉 所有分块加密测试通过!")
        sys.exit(0)
    else:
        logger.error("\n❌ 部分分块加密测试失败，请检查日志")
        sys.exit(1)
