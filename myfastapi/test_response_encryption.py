#!/usr/bin/env python3
# myfastapi/test_response_encryption.py
"""
测试响应加密功能
"""
import sys
import os
import time
import json
import base64
import requests
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到系统路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.backends import default_backend
except ImportError:
    logger.error("未安装cryptography库，请使用 pip install cryptography 安装")
    sys.exit(1)

# 测试参数
API_URL = "http://localhost:8000"  # 修改为实际的API地址

def generate_key_pair():
    """生成RSA密钥对"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
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

def base64_to_bytes(base64_str):
    """将Base64字符串转换为bytes"""
    return base64.b64decode(base64_str)

def decrypt_with_private_key(encrypted_data, private_key):
    """使用私钥解密数据"""
    # 确保是RSA私钥
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ValueError("提供的私钥不是RSA类型")
        
    padding_algorithm = padding.OAEP(
        mgf=padding.MGF1(hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
    
    # 如果输入是字符串，转换为bytes
    if isinstance(encrypted_data, str):
        encrypted_bytes = base64_to_bytes(encrypted_data)
    else:
        encrypted_bytes = encrypted_data
    
    decrypted_data = private_key.decrypt(
        encrypted_bytes,
        padding_algorithm
    )
    
    try:
        # 尝试解析为JSON
        return json.loads(decrypted_data.decode())
    except json.JSONDecodeError:
        # 如果不是JSON，返回原始解密数据
        return decrypted_data

def encrypt_data(data, server_public_key_pem):
    """使用服务器公钥加密数据"""
    # 格式化公钥
    if not server_public_key_pem.startswith("-----BEGIN PUBLIC KEY-----"):
        server_public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{server_public_key_pem}\n-----END PUBLIC KEY-----"
    
    # 加载公钥
    public_key = serialization.load_pem_public_key(
        server_public_key_pem.encode(),
        backend=default_backend()
    )
    
    # 确保是RSA公钥
    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ValueError("服务器公钥不是RSA类型")
    
    # 加密数据
    padding_algorithm = padding.OAEP(
        mgf=padding.MGF1(hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
    
    encrypted_data = public_key.encrypt(
        json.dumps(data).encode(),
        padding_algorithm
    )
    
    return base64.b64encode(encrypted_data).decode()

def run_test():
    """运行集成测试"""
    try:
        # 生成客户端密钥对
        logger.info("生成客户端密钥对...")
        public_pem, private_pem, private_key = generate_key_pair()
        
        # 获取服务器公钥
        logger.info("获取服务器公钥...")
        res = requests.get(f"{API_URL}/security-info")
        if not res.ok:
            logger.error(f"获取服务器公钥失败: {res.status_code} - {res.text}")
            return False
        
        server_data = res.json()
        server_public_key = server_data["public_key"]
        logger.info(f"获取到服务器公钥: {server_public_key[:30]}...")
        
        # 注册客户端公钥
        logger.info("注册客户端公钥...")
        res = requests.post(
            f"{API_URL}/register-client-key",
            json={
                "client_id": "test-client",
                "public_key": public_pem
            }
        )
        
        if not res.ok:
            logger.error(f"注册客户端公钥失败: {res.status_code} - {res.text}")
            return False
        
        logger.info("客户端公钥注册成功")
        
        # 创建测试请求
        test_data = {
            "uid": "test-user",
            "code": "123456"
        }
        
        timestamp = int(time.time() * 1000)
        encrypted_data = encrypt_data(test_data, server_public_key)
        
        # 发送加密请求
        logger.info("发送加密请求...")
        res = requests.post(
            f"{API_URL}/verify-otp",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "test-client",
                "X-Timestamp": str(timestamp),
                "X-Signature": "frontend"
            },
            json={
                "encrypted_data": encrypted_data,
                "timestamp": timestamp,
                "signature": "frontend"
            }
        )
        
        if not res.ok:
            logger.error(f"请求失败: {res.status_code} - {res.text}")
            return False
        
        # 尝试解密响应
        logger.info("解密响应...")
        response_data = res.json()
        
        if "data" in response_data and "timestamp" in response_data and "signature" in response_data:
            try:
                decrypted_data = decrypt_with_private_key(response_data["data"], private_key)
                logger.info(f"解密成功: {decrypted_data}")
                return True
            except Exception as e:
                logger.error(f"解密响应失败: {str(e)}")
                return False
        else:
            logger.error(f"响应格式不正确: {response_data}")
            return False
    
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        return False

def test_large_response_hybrid_encryption():
    """测试大响应数据的混合加密"""
    logger.info("开始测试大数据的混合加密...")
    
    try:
        # 生成客户端密钥对
        logger.info("生成客户端密钥对...")
        public_pem, private_pem, private_key = generate_key_pair()
        client_id = f"test-client-{int(time.time())}"
        
        # 获取服务器公钥
        logger.info("获取服务器公钥...")
        res = requests.get(f"{API_URL}/security-info")
        if not res.ok:
            logger.error(f"获取服务器公钥失败: {res.status_code} - {res.text}")
            return False
        
        server_data = res.json()
        server_public_key = server_data["public_key"]
        logger.info(f"获取到服务器公钥: {server_public_key[:30]}...")
        
        # 注册客户端公钥
        logger.info("注册客户端公钥...")
        res = requests.post(
            f"{API_URL}/register-client-key",
            json={
                "client_id": client_id,
                "public_key": public_pem
            }
        )
        
        if not res.ok:
            logger.error(f"注册客户端公钥失败: {res.status_code} - {res.text}")
            return False
        
        logger.info("客户端公钥注册成功")
        
        # 构造一个大数据响应测试 - 请求tradingcommand端点，这会生成大于RSA限制的响应
        large_data = {
            "command": "test",
            "params": {
                "data": "x" * 500,  # 添加足够大的数据以触发混合加密
                "test": True,
                "timestamp": int(time.time())
            }
        }
        
        timestamp = int(time.time() * 1000)
        encrypted_data = encrypt_data(large_data, server_public_key)
        
        # 发送请求
        logger.info("发送包含大数据的加密请求...")
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": client_id,
            "X-Timestamp": str(timestamp),
            "X-Signature": "frontend"
        }
        
        request_body = {
            "encrypted_data": encrypted_data,
            "timestamp": timestamp,
            "signature": "frontend"
        }
        
        response = requests.post(
            f"{API_URL}/tradingcommand",
            json=request_body,
            headers=headers
        )
        
        if response.status_code != 200:
            logger.error(f"请求失败: {response.status_code} - {response.text}")
            return False
        
        # 解析响应
        logger.info("解析响应...")
        response_data = response.json()
        
        # 尝试解析为混合加密格式
        try:
            encrypted_response_data = response_data["data"]
            
            # 尝试解析为JSON (混合加密的响应是JSON字符串)
            try:
                hybrid_data = json.loads(encrypted_response_data)
                
                # 检查是否是混合加密格式
                if "encryption_method" in hybrid_data and hybrid_data["encryption_method"] == "hybrid":
                    logger.info("检测到混合加密响应 - 验证成功!")
                    return True
                else:
                    logger.warning("响应使用了非混合加密格式")
                    # 尝试常规RSA解密
                    try:
                        decrypted_data = decrypt_with_private_key(encrypted_response_data, private_key)
                        logger.info("使用标准RSA解密成功")
                        return True
                    except Exception as rsa_error:
                        logger.error(f"RSA解密失败: {str(rsa_error)}")
                        return False
            except json.JSONDecodeError:
                # 不是JSON格式，可能是常规RSA加密
                try:
                    decrypted_data = decrypt_with_private_key(encrypted_response_data, private_key)
                    logger.info("标准RSA解密成功")
                    return True
                except Exception as rsa_error:
                    logger.error(f"解密失败: {str(rsa_error)}")
                    return False
        except Exception as e:
            logger.error(f"处理响应失败: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"测试混合加密失败: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("开始测试响应加密功能...")
    
    # 测试标准加密
    logger.info("\n== 测试标准响应加密 ==")
    standard_success = run_test()
    
    # 测试混合加密（处理大数据）
    logger.info("\n== 测试混合加密（处理大数据） ==")
    hybrid_success = test_large_response_hybrid_encryption()
    
    # 汇总测试结果
    if standard_success and hybrid_success:
        logger.info("\n✅ 所有测试通过!")
        sys.exit(0)
    elif standard_success:
        logger.info("\n❗ 标准加密测试通过，但混合加密测试失败")
        sys.exit(1)
    elif hybrid_success:
        logger.info("\n❗ 混合加密测试通过，但标准加密测试失败")
        sys.exit(1)
    else:
        logger.error("\n❌ 所有测试均失败!")
        sys.exit(1)
