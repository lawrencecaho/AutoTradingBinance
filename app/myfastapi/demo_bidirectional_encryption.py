#!/usr/bin/env python3
# myfastapi/demo_bidirectional_encryption.py
"""
双向加密通信演示脚本

本脚本模拟前端和后端之间的双向加密通信流程，用于演示和测试双向加密机制。
脚本包括：
1. 生成客户端密钥对（模拟前端）
2. 获取服务器公钥
3. 注册客户端公钥
4. 使用服务器公钥加密请求
5. 使用客户端私钥解密响应

此文件是独立的测试/演示工具，可以随时删除而不影响系统功能。
"""

import sys
import os
import time
import json
import base64
import requests
from pathlib import Path
import logging
import argparse

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

class BidirectionalEncryptionDemo:
    """双向加密通信演示类"""
    
    def __init__(self, api_url="http://localhost:8000", client_id="demo-client"):
        """初始化演示类"""
        self.api_url = api_url
        self.client_id = client_id
        self.server_public_key = None
        self.client_public_key = None
        self.client_private_key = None
        
    def generate_client_keys(self):
        """生成客户端密钥对（模拟前端行为）"""
        logger.info("生成客户端密钥对...")
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # 导出公钥为PEM格式
        self.client_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        
        # 保存私钥引用，用于后续解密
        self.client_private_key = private_key
        
        logger.info("客户端密钥对生成成功")
        return True
        
    def get_server_public_key(self):
        """获取服务器公钥"""
        logger.info(f"从 {self.api_url}/security-info 获取服务器公钥...")
        try:
            res = requests.get(f"{self.api_url}/security-info")
            if not res.ok:
                logger.error(f"获取服务器公钥失败: {res.status_code} - {res.text}")
                return False
            
            server_data = res.json()
            self.server_public_key = server_data["public_key"]
            logger.info(f"获取到服务器公钥: {self.server_public_key[:30]}...")
            return True
        except Exception as e:
            logger.error(f"获取服务器公钥出错: {str(e)}")
            return False
    
    def register_client_public_key(self):
        """向服务器注册客户端公钥"""
        if not self.client_public_key:
            logger.error("客户端公钥不存在，请先生成密钥对")
            return False
            
        logger.info(f"向 {self.api_url}/register-client-key 注册客户端公钥...")
        try:
            res = requests.post(
                f"{self.api_url}/register-client-key",
                json={
                    "client_id": self.client_id,
                    "public_key": self.client_public_key
                }
            )
            
            if not res.ok:
                logger.error(f"注册客户端公钥失败: {res.status_code} - {res.text}")
                return False
            
            logger.info("客户端公钥注册成功")
            return True
        except Exception as e:
            logger.error(f"注册客户端公钥出错: {str(e)}")
            return False
    
    def encrypt_request_data(self, data):
        """使用服务器公钥加密请求数据"""
        if not self.server_public_key:
            logger.error("服务器公钥不存在，请先获取服务器公钥")
            return None
            
        try:
            # 格式化公钥
            server_public_key_pem = self.server_public_key
            if not server_public_key_pem.startswith("-----BEGIN PUBLIC KEY-----"):
                server_public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{server_public_key_pem}\n-----END PUBLIC KEY-----"
            
            # 加载公钥
            public_key = serialization.load_pem_public_key(
                server_public_key_pem.encode(),
                backend=default_backend()
            )
            
            # 确保是RSA公钥
            if not isinstance(public_key, rsa.RSAPublicKey):
                logger.error("服务器公钥不是RSA类型")
                return None
            
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
        except Exception as e:
            logger.error(f"加密请求数据失败: {str(e)}")
            return None
    
    def decrypt_response(self, encrypted_data):
        """使用客户端私钥解密响应数据"""
        if not self.client_private_key:
            logger.error("客户端私钥不存在，请先生成密钥对")
            return None
            
        try:
            # 确保是RSA私钥
            if not isinstance(self.client_private_key, rsa.RSAPrivateKey):
                logger.error("客户端私钥不是RSA类型")
                return None
                
            padding_algorithm = padding.OAEP(
                mgf=padding.MGF1(hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
            
            decrypted_data = self.client_private_key.decrypt(
                base64.b64decode(encrypted_data),
                padding_algorithm
            )
            
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"解密响应数据失败: {str(e)}")
            return None
    
    def send_encrypted_request(self, endpoint, data):
        """发送加密请求并解密响应"""
        if not self.server_public_key:
            logger.error("服务器公钥不存在，请先获取服务器公钥")
            return None
            
        timestamp = int(time.time() * 1000)
        encrypted_data = self.encrypt_request_data(data)
        
        if not encrypted_data:
            logger.error("加密请求数据失败")
            return None
            
        logger.info(f"向 {endpoint} 发送加密请求...")
        try:
            res = requests.post(
                f"{self.api_url}{endpoint}",
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": self.client_id,
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
                return None
            
            logger.info("请求成功，尝试解密响应...")
            response_data = res.json()
            
            # 检查响应是否是加密格式
            if "data" in response_data and "timestamp" in response_data and "signature" in response_data:
                decrypted_data = self.decrypt_response(response_data["data"])
                if decrypted_data:
                    logger.info("响应解密成功")
                    return decrypted_data
                else:
                    logger.error("响应解密失败")
                    return response_data
            else:
                logger.warning("响应不是加密格式")
                return response_data
        except Exception as e:
            logger.error(f"发送请求出错: {str(e)}")
            return None
    
    def run_demo(self):
        """运行完整演示流程"""
        logger.info("===== 开始双向加密通信演示 =====")
        
        # 1. 生成客户端密钥对
        if not self.generate_client_keys():
            logger.error("生成客户端密钥对失败，演示终止")
            return False
        
        # 2. 获取服务器公钥
        if not self.get_server_public_key():
            logger.error("获取服务器公钥失败，演示终止")
            return False
        
        # 3. 注册客户端公钥
        if not self.register_client_public_key():
            logger.error("注册客户端公钥失败，演示终止")
            return False
        
        # 4. 发送加密请求
        logger.info("发送测试请求...")
        test_data = {
            "uid": "test-user",
            "code": "123456"
        }
        
        response = self.send_encrypted_request("/verify-otp", test_data)
        if response:
            logger.info(f"得到解密响应: {json.dumps(response, indent=2)}")
            logger.info("===== 双向加密通信演示成功 =====")
            return True
        else:
            logger.error("请求失败，演示终止")
            return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="双向加密通信演示")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务器URL")
    parser.add_argument("--client", default="demo-client", help="客户端ID")
    
    args = parser.parse_args()
    
    demo = BidirectionalEncryptionDemo(
        api_url=args.url,
        client_id=args.client
    )
    
    success = demo.run_demo()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
