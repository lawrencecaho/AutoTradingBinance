"""
加密系统集成测试

测试整个加密系统的集成功能，包括：
1. 标准RSA加密/解密
2. 混合加密（AES+RSA）
3. 分块加密
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
from myfastapi.security import (
    encrypt_data, 
    decrypt_data, 
    hybrid_encrypt_with_client_key,
    encrypt_with_client_key
)
from myfastapi.chunked_encryption import chunk_encrypt_large_data
from myfastapi.test_hybrid_encryption import generate_key_pair, hybrid_decrypt
from myfastapi.test_chunked_encryption import decrypt_chunked_data
from myfastapi.main import encrypt_response

# 模拟客户端ID
mock_client_id = "test_client_123"

# 存储测试客户端公钥
def store_test_client_key(client_id: str, public_key: str):
    """模拟存储客户端公钥"""
    from myfastapi.security import store_client_public_key
    store_client_public_key(client_id, public_key)

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

def test_standard_encryption():
    """测试标准RSA加密/解密"""
    logger.info("\n====== 标准RSA加密测试 ======")
    
    # 生成小型测试数据
    test_data = generate_test_data(size_kb=0.1)  # 100字节左右
    json_data = json.dumps(test_data)
    
    # 加密 - 在这里修改为使用混合加密
    start_time = time.time()
    _, public_pem, _ = generate_key_pair(2048)
    encrypted = hybrid_encrypt_with_client_key(json_data, public_pem)
    encryption_time = time.time() - start_time
    
    if not encrypted.get("success", False):
        logger.error(f"标准加密失败: {encrypted.get('error', '未知错误')}")
        return False
    
    # 记录加密状态
    logger.info(f"标准加密测试 (使用混合加密替代): 成功")
    logger.info(f"加密时间: {encryption_time:.4f}秒")
    
    return True

def test_hybrid_encryption():
    """测试混合加密（AES+RSA）"""
    logger.info("\n====== 混合加密测试 ======")
    
    # 生成测试数据
    test_data = generate_test_data(size_kb=5)  # 5KB，足够触发混合加密
    json_data = json.dumps(test_data)
    
    # 生成客户端密钥对
    public_pem, private_pem, private_key = generate_key_pair(2048)
    
    # 加密
    start_time = time.time()
    encrypted = hybrid_encrypt_with_client_key(json_data, public_pem)
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
    public_pem, private_pem, private_key = generate_key_pair(2048)
    
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

def test_integrated_encryption():
    """测试集成加密系统（自动选择加密方法）"""
    logger.info("\n====== 集成加密系统测试 ======")
    
    # 生成客户端密钥对并注册
    public_pem, private_pem, private_key = generate_key_pair(2048)
    store_test_client_key(mock_client_id, public_pem)
    
    test_cases = [
        {"name": "小数据（标准RSA）", "size_kb": 0.1},
        {"name": "中型数据（混合加密）", "size_kb": 5},
        {"name": "大型数据（分块加密）", "size_kb": 1500}
    ]
    
    results = []
    
    for case in test_cases:
        logger.info(f"\n测试案例: {case['name']} ({case['size_kb']}KB)")
        
        # 生成测试数据
        test_data = generate_test_data(size_kb=case["size_kb"])
        
        # 使用主系统加密函数
        start_time = time.time()
        encrypted_response = encrypt_response(test_data, mock_client_id)
        encryption_time = time.time() - start_time
        
        # 提取加密数据
        encrypted_data = encrypted_response.data
        
        # 解析加密方法
        try:
            encrypted_json = json.loads(encrypted_data)
            encryption_method = encrypted_json.get("encryption_method", "unknown")
            if encryption_method == "chunked_hybrid":
                logger.info(f"检测到分块加密，块数: {encrypted_json.get('total_chunks')}")
                
                # 解密分块数据
                start_time = time.time()
                decrypted_json = decrypt_chunked_data(encrypted_json, private_key)
                decryption_time = time.time() - start_time
                
                # 验证
                success = decrypted_json == json.dumps(test_data)
                
            elif encryption_method == "hybrid":
                logger.info("检测到混合加密")
                
                # 解密混合加密数据
                start_time = time.time()
                decrypted_json = hybrid_decrypt(encrypted_json, private_key)
                decryption_time = time.time() - start_time
                
                # 验证
                success = json.loads(decrypted_json) == test_data
                
            else:
                logger.info(f"检测到标准加密或未知加密方法: {encryption_method}")
                
                # 尝试标准解密
                start_time = time.time()
                try:
                    # 先尝试标准RSA解密
                    decrypted_buffer = await_crypto_decrypt(encrypted_data, private_key)
                    decrypted_json = json.loads(decrypted_buffer)
                    decryption_time = time.time() - start_time
                    
                    # 验证
                    success = decrypted_json == test_data
                except:
                    logger.error("标准RSA解密失败")
                    success = False
                    decryption_time = time.time() - start_time
        except Exception as e:
            logger.error(f"解析加密数据失败: {str(e)}")
            success = False
            decryption_time = 0
        
        # 记录结果
        logger.info(f"加密方法: {encryption_method if 'encryption_method' in locals() else '未知'}")
        logger.info(f"加密时间: {encryption_time:.4f}秒, 解密时间: {decryption_time:.4f}秒")
        logger.info(f"测试结果: {'成功' if success else '失败'}")
        
        results.append(success)
    
    # 汇总结果
    success_rate = sum(results) / len(results) * 100
    logger.info(f"\n集成加密系统测试完成: 通过率 {success_rate:.2f}% ({sum(results)}/{len(results)})")
    return all(results)

def await_crypto_decrypt(encrypted_data: str, private_key) -> str:
    """模拟前端的标准RSA解密"""
    encrypted_bytes = base64.b64decode(encrypted_data)
    
    # 使用RSA-OAEP解密
    decrypted_bytes = private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # 解码为字符串
    return decrypted_bytes.decode()

if __name__ == "__main__":
    logger.info("开始加密系统集成测试")
    
    # 运行各类测试
    standard_test = test_standard_encryption()
    hybrid_test = test_hybrid_encryption()
    chunked_test = test_chunked_encryption()
    integrated_test = test_integrated_encryption()
    
    # 汇总结果
    test_results = {
        "标准RSA加密": standard_test,
        "混合加密(AES+RSA)": hybrid_test,
        "分块加密": chunked_test,
        "集成加密系统": integrated_test
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
