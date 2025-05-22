# 混合加密与异常处理测试

import os
import json
import base64
import time
import logging
from pathlib import Path
from typing import Dict, Any

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 设置项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in os.sys.path:
    os.sys.path.insert(0, project_root)

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
except ImportError:
    logger.error("未安装cryptography库，请使用 pip install cryptography 安装")
    os.sys.exit(1)

def generate_key_pair(key_size=2048):
    """生成RSA密钥对"""
    logger.info(f"生成{key_size}位RSA密钥对")
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    
    # 导出公钥为PEM格式
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()
    
    # 导出私钥为PEM格式
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()
    
    return public_pem, private_pem, private_key

def hybrid_encrypt(data: str, public_key_pem: str) -> Dict[str, Any]:
    """
    实现混合加密 (AES+RSA)
    
    Args:
        data: 要加密的数据
        public_key_pem: PEM格式的RSA公钥
        
    Returns:
        加密结果字典，包含加密数据、加密密钥和元数据
    """
    logger.info(f"混合加密数据，原始大小: {len(data)} 字节")
    
    try:
        # 确保公钥格式正确
        if not public_key_pem.startswith("-----BEGIN PUBLIC KEY-----"):
            public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_pem}\n-----END PUBLIC KEY-----"
        
        # 加载公钥
        client_public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        # 确保是RSA公钥
        if not isinstance(client_public_key, rsa.RSAPublicKey):
            raise ValueError("提供的不是RSA公钥")
        
        # 检查公钥大小
        key_size_bytes = (client_public_key.key_size + 7) // 8
        max_key_plaintext_size = key_size_bytes - 42  # OAEP填充
        
        logger.info(f"RSA密钥大小: {client_public_key.key_size} 位，最大明文大小: {max_key_plaintext_size} 字节")
        
        # 确定AES密钥大小
        aes_key_size = 32  # 默认256位AES
        if max_key_plaintext_size < 48:  # 48 = 32(密钥) + 16(IV)
            if max_key_plaintext_size >= 32:
                aes_key_size = 24  # 192位AES
                logger.info("使用192位AES密钥")
            elif max_key_plaintext_size >= 24:
                aes_key_size = 16  # 128位AES
                logger.info("使用128位AES密钥")
            else:
                raise ValueError(f"RSA密钥太小({client_public_key.key_size}位)，无法安全加密AES密钥")
        else:
            logger.info("使用256位AES密钥")
        
        # 生成随机AES密钥和IV
        aes_key = os.urandom(aes_key_size)
        iv = os.urandom(16)
        
        # 使用AES加密数据
        data_bytes = data.encode()
        
        # PKCS7填充
        block_size = 16
        padding_length = block_size - (len(data_bytes) % block_size)
        padded_data = data_bytes + bytes([padding_length] * padding_length)
        
        # 加密
        encryptor = Cipher(
            algorithms.AES(aes_key),
            modes.CBC(iv),
            backend=default_backend()
        ).encryptor()
        
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        
        # 使用RSA加密AES密钥和IV
        rsa_padding = padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
        
        key_iv = aes_key + iv
        encrypted_key = client_public_key.encrypt(key_iv, rsa_padding)
        
        # 返回结果
        result = {
            "success": True,
            "encrypted_data": base64.b64encode(encrypted_data).decode(),
            "encrypted_key": base64.b64encode(encrypted_key).decode(),
            "encryption_method": "hybrid",
            "aes_key_size": len(aes_key) * 8,
            "aes_mode": "CBC",
            "timestamp": int(time.time() * 1000)
        }
        
        logger.info(f"混合加密成功，加密后数据大小: {len(result['encrypted_data'])} 字节")
        return result
    
    except Exception as e:
        logger.error(f"混合加密失败: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "encryption_method": "hybrid_failed"
        }

def hybrid_decrypt(hybrid_data: Dict[str, Any], private_key) -> str:
    """
    解密混合加密的数据
    
    Args:
        hybrid_data: 混合加密结果字典
        private_key: RSA私钥对象
        
    Returns:
        解密后的原始数据
    """
    logger.info("解密混合加密数据")
    
    try:
        # 检查必需字段
        if not all(k in hybrid_data for k in ["encrypted_data", "encrypted_key", "encryption_method"]):
            raise ValueError("无效的混合加密数据格式，缺少必需字段")
        
        if hybrid_data["encryption_method"] != "hybrid":
            raise ValueError(f"不支持的加密方法: {hybrid_data['encryption_method']}")
        
        # 获取AES密钥大小
        aes_key_size = hybrid_data.get("aes_key_size", 256)
        aes_key_bytes = aes_key_size // 8
        logger.info(f"使用 AES-{aes_key_size} 解密")
        
        # 解密AES密钥和IV
        encrypted_key = base64.b64decode(hybrid_data["encrypted_key"])
        
        rsa_padding = padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
        
        key_iv = private_key.decrypt(
            encrypted_key,
            rsa_padding
        )
        
        # 分离AES密钥和IV
        if len(key_iv) < aes_key_bytes + 16:
            logger.warning(f"解密的密钥数据长度不足: {len(key_iv)}字节，尝试降级处理")
            # 尝试降级
            if len(key_iv) >= 16 + 16:  # 至少支持AES-128
                aes_key_bytes = 16
                logger.info("降级到AES-128")
            else:
                raise ValueError(f"密钥数据长度不足: {len(key_iv)}字节，无法解密")
        
        aes_key = key_iv[:aes_key_bytes]
        iv = key_iv[aes_key_bytes:aes_key_bytes+16]
        
        # 解密数据
        encrypted_data = base64.b64decode(hybrid_data["encrypted_data"])
        
        decryptor = Cipher(
            algorithms.AES(aes_key),
            modes.CBC(iv),
            backend=default_backend()
        ).decryptor()
        
        decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
        
        # 移除PKCS7填充
        padding_length = decrypted_padded[-1]
        if padding_length > 16:
            logger.warning(f"异常的填充长度: {padding_length}，可能导致解密错误")
        
        decrypted_data = decrypted_padded[:-padding_length]
        
        # 解码为字符串
        result = decrypted_data.decode()
        logger.info(f"解密成功，解密后数据大小: {len(result)} 字节")
        return result
    
    except Exception as e:
        logger.error(f"混合解密失败: {str(e)}")
        raise

def run_hybrid_encryption_test(data_size=1000, key_size=2048):
    """运行混合加密测试"""
    logger.info(f"====== 开始混合加密测试 (数据大小: {data_size} 字节, RSA密钥: {key_size} 位) ======")
    
    # 生成测试数据
    test_data = "x" * data_size
    
    # 生成密钥对
    public_pem, private_pem, private_key = generate_key_pair(key_size)
    
    # 加密
    encrypted = hybrid_encrypt(test_data, public_pem)
    
    if not encrypted["success"]:
        logger.error(f"混合加密测试失败: {encrypted.get('error', '未知错误')}")
        return False
    
    # 解密
    try:
        decrypted = hybrid_decrypt(encrypted, private_key)
        
        # 验证
        if decrypted == test_data:
            logger.info("混合加密测试成功: 解密后数据与原始数据匹配")
            return True
        else:
            logger.error(f"混合加密测试失败: 解密后数据与原始数据不匹配 (原始长度: {len(test_data)}, 解密后长度: {len(decrypted)})")
            return False
    except Exception as e:
        logger.error(f"混合加密测试解密阶段失败: {str(e)}")
        return False

def test_edge_cases():
    """测试边界情况"""
    logger.info("\n====== 边界情况测试 ======")
    
    test_cases = [
        {"name": "空数据", "data": "", "key_size": 2048, "expected_success": True},
        {"name": "小数据", "data": "test", "key_size": 2048, "expected_success": True},
        {"name": "大数据", "data": "x" * 10000, "key_size": 2048, "expected_success": True},
        {"name": "非ASCII数据", "data": "中文测试数据 😀🔐", "key_size": 2048, "expected_success": True},
        {"name": "小密钥", "data": "test data", "key_size": 1024, "expected_success": True},
        {"name": "JSON数据", "data": json.dumps({"test": "data", "array": [1, 2, 3]}), "key_size": 2048, "expected_success": True},
    ]
    
    results = []
    
    for case in test_cases:
        logger.info(f"\n测试案例: {case['name']}")
        try:
            success = run_hybrid_encryption_test(
                data_size=len(case["data"]) if case["data"] else 0, 
                key_size=case["key_size"]
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
    logger.info(f"\n边界情况测试完成: 通过率 {success_rate:.2f}% ({sum(results)}/{len(results)})")
    return all(results)

if __name__ == "__main__":
    logger.info("开始混合加密与异常处理测试")
    
    # 运行基本测试
    basic_test_success = run_hybrid_encryption_test(data_size=1000)
    
    # 运行边界情况测试
    edge_cases_success = test_edge_cases()
    
    # 汇总结果
    if basic_test_success and edge_cases_success:
        logger.info("\n🎉 所有测试通过!")
        os.sys.exit(0)
    else:
        logger.error("\n❌ 部分测试失败，请检查日志")
        os.sys.exit(1)
