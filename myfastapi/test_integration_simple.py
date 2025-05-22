"""
简化版集成测试

测试混合加密和分块加密功能
"""

import os
import sys
import json
import base64
import time
import logging
import random
import string
from pathlib import Path
from typing import Dict, Any, List, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入项目模块
from myfastapi.test_hybrid_encryption import generate_key_pair, hybrid_encrypt, hybrid_decrypt
from myfastapi.chunked_encryption import chunk_encrypt_large_data
from myfastapi.test_chunked_encryption import decrypt_chunked_data

def generate_test_data(size_kb: int) -> Dict[str, Any]:
    """生成指定大小的测试JSON数据"""
    logger.info(f"生成 {size_kb}KB 的测试JSON数据")
    
    # 创建带有嵌套结构的数据
    data = {
        "meta": {
            "timestamp": int(time.time() * 1000),
            "version": "1.0",
            "test_id": f"test_{random.randint(10000, 99999)}",
            "size": f"{size_kb}KB"
        },
        "data": [],
        "settings": {
            "encryption": "enabled",
            "compression": "disabled",
            "chunking": size_kb > 1024
        }
    }
    
    # 添加足够的数据到达目标大小
    chars = string.ascii_letters + string.digits
    target_size = size_kb * 1024
    current_size = len(json.dumps(data))
    
    # 创建随机数据项
    while current_size < target_size:
        # 生成随机字符串
        item_id = ''.join(random.choice(chars) for _ in range(8))
        item_value = ''.join(random.choice(chars) for _ in range(random.randint(20, 100)))
        
        # 添加到数据列表
        data["data"].append({
            "id": item_id,
            "value": item_value,
            "attributes": {
                "created": int(time.time() * 1000),
                "modified": int(time.time() * 1000),
                "status": random.choice(["active", "pending", "archived"])
            }
        })
        
        # 重新计算大小
        current_size = len(json.dumps(data))
    
    # 验证大小
    actual_size = len(json.dumps(data))
    logger.info(f"生成的测试JSON数据大小: {actual_size} 字节")
    
    return data

def test_hybrid_encryption():
    """测试混合加密（AES+RSA）"""
    logger.info("\n====== 混合加密测试 ======")
    
    # 生成测试数据
    test_data = generate_test_data(size_kb=5)  # 5KB，足够触发混合加密
    json_data = json.dumps(test_data)
    
    # 生成客户端密钥对
    public_pem, _, private_key = generate_key_pair(2048)
    
    # 加密
    start_time = time.time()
    encrypted = hybrid_encrypt(json_data, public_pem)
    encryption_time = time.time() - start_time
    
    if not encrypted.get("success", False):
        logger.error(f"混合加密失败: {encrypted.get('error', '未知错误')}")
        return False
    
    # 解密
    start_time = time.time()
    decrypted = hybrid_decrypt(encrypted, private_key)
    decryption_time = time.time() - start_time
    
    # 验证
    success = decrypted == json_data
    
    logger.info(f"混合加密测试: {'成功' if success else '失败'}")
    logger.info(f"加密时间: {encryption_time:.4f}秒, 解密时间: {decryption_time:.4f}秒")
    
    return success

def test_chunked_encryption():
    """测试分块加密"""
    logger.info("\n====== 分块加密测试 ======")
    
    # 生成大型测试数据
    test_data = generate_test_data(size_kb=1500)  # 1.5MB，足够触发分块加密
    json_data = json.dumps(test_data)
    
    # 生成客户端密钥对
    public_pem, _, private_key = generate_key_pair(2048)
    
    # 指定块大小
    chunk_size = 256 * 1024  # 256KB
    
    # 加密
    start_time = time.time()
    encrypted = chunk_encrypt_large_data(json_data, public_pem, chunk_size)
    encryption_time = time.time() - start_time
    
    if not encrypted.get("success", False):
        logger.error(f"分块加密失败: {encrypted.get('error', '未知错误')}")
        return False
    
    # 解密
    start_time = time.time()
    decrypted = decrypt_chunked_data(encrypted, private_key)
    decryption_time = time.time() - start_time
    
    # 验证
    success = decrypted == json_data
    
    logger.info(f"分块加密测试: {'成功' if success else '失败'}")
    logger.info(f"加密时间: {encryption_time:.4f}秒, 解密时间: {decryption_time:.4f}秒")
    logger.info(f"分块数: {encrypted['total_chunks']}, 块大小: {chunk_size/1024:.2f}KB")
    
    return success

if __name__ == "__main__":
    logger.info("开始简化版加密系统集成测试")
    
    # 运行混合加密测试
    hybrid_test = test_hybrid_encryption()
    
    # 运行分块加密测试
    chunked_test = test_chunked_encryption()
    
    # 汇总结果
    test_results = {
        "混合加密(AES+RSA)": hybrid_test,
        "分块加密": chunked_test
    }
    
    # 打印汇总
    logger.info("\n====== 测试结果汇总 ======")
    for test_name, result in test_results.items():
        logger.info(f"{test_name}: {'✅ 通过' if result else '❌ 失败'}")
    
    # 整体结果
    if all(test_results.values()):
        logger.info("\n🎉 所有加密系统测试通过!")
        sys.exit(0)
    else:
        logger.error("\n❌ 部分加密系统测试失败，请检查日志")
        sys.exit(1)
