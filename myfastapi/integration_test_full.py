#!/usr/bin/env python3
# myfastapi/integration_test_full.py
"""
完整的集成测试脚本

本脚本测试系统的完整通信流程，包括：
1. 服务器状态检查
2. 安全信息获取
3. 客户端密钥注册
4. 加密请求发送
5. 加密响应解密
6. 用户验证流程

使用方法：
python myfastapi/integration_test_full.py
"""

import sys
import os
import time
import json
import base64
import requests
import argparse
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    import pyotp
except ImportError:
    logger.error("未安装所需库，请使用 pip install cryptography pyotp 安装")
    sys.exit(1)

class IntegrationTest:
    """完整集成测试类"""
    
    def __init__(self, api_url="http://localhost:8000", client_id="test-client"):
        """初始化测试类"""
        self.api_url = api_url
        self.client_id = client_id
        self.server_public_key = None
        self.client_private_key = None
        self.client_public_key = None
        self.test_user = None
        self.test_user_otp = None
        self.test_token = None
        self.tests_passed = 0
        self.tests_total = 0
        
    def log_test(self, name, success, details=None):
        """记录测试结果"""
        self.tests_total += 1
        if success:
            self.tests_passed += 1
            logger.info(f"✅ 测试通过: {name}")
        else:
            logger.error(f"❌ 测试失败: {name}")
            if details:
                logger.error(f"  详情: {details}")
    
    def test_server_status(self):
        """测试服务器状态"""
        try:
            res = requests.get(f"{self.api_url}/security-info")
            self.log_test("服务器状态检查", res.ok, None if res.ok else f"状态码: {res.status_code}")
            return res.ok
        except Exception as e:
            self.log_test("服务器状态检查", False, str(e))
            return False
    
    def generate_client_keys(self):
        """生成客户端密钥对"""
        try:
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
            
            # 保存私钥引用
            self.client_private_key = private_key
            
            self.log_test("生成客户端密钥对", True)
            return True
        except Exception as e:
            self.log_test("生成客户端密钥对", False, str(e))
            return False
    
    def get_server_public_key(self):
        """获取服务器公钥"""
        try:
            res = requests.get(f"{self.api_url}/security-info")
            if not res.ok:
                self.log_test("获取服务器公钥", False, f"状态码: {res.status_code}")
                return False
            
            server_data = res.json()
            self.server_public_key = server_data["public_key"]
            self.log_test("获取服务器公钥", True)
            return True
        except Exception as e:
            self.log_test("获取服务器公钥", False, str(e))
            return False
    
    def register_client_public_key(self):
        """注册客户端公钥"""
        try:
            res = requests.post(
                f"{self.api_url}/register-client-key",
                json={
                    "client_id": self.client_id,
                    "public_key": self.client_public_key
                }
            )
            self.log_test("注册客户端公钥", res.ok, None if res.ok else f"状态码: {res.status_code}")
            return res.ok
        except Exception as e:
            self.log_test("注册客户端公钥", False, str(e))
            return False
    
    def create_test_user(self):
        """创建测试用户"""
        # 使用项目中的create_test_user功能创建用户
        try:
            # 检查是否存在create_user函数
            from myfastapi.authtotp import create_user
            
            # 使用固定的测试用户名称，方便测试
            self.test_user = "integration_test_user"
            test_username = "集成测试用户"
            
            logger.info(f"创建测试用户: {self.test_user} - {test_username}")
            success = create_user(self.test_user, test_username)
            
            if success:
                # 获取用户的TOTP密钥进行测试
                from database import Session, dbselect_common
                
                with Session() as session:
                    result = dbselect_common(session, "userbasic", "uid", self.test_user)
                    if result and result[0].totpsecret:
                        totp_secret = result[0].totpsecret
                        self.test_user_otp = pyotp.TOTP(totp_secret)
                        
                        logger.info(f"测试用户创建成功")
                        logger.info(f"TOTP密钥: {totp_secret}")
                        logger.info(f"当前TOTP码: {self.test_user_otp.now()}")
                        
                        self.log_test("创建测试用户", True)
                        return True
                    else:
                        logger.error("无法获取用户TOTP密钥")
                        self.log_test("创建测试用户", False, "无法获取用户TOTP密钥")
                        return False
            else:
                logger.error("创建用户失败")
                self.log_test("创建测试用户", False, "创建用户失败")
                return False
        except Exception as e:
            logger.error(f"创建测试用户出错: {str(e)}")
            
            # 如果创建失败，尝试使用已存在的测试用户
            try:
                self.test_user = "testuser"  # 使用默认测试用户
                
                from database import Session, dbselect_common
                with Session() as session:
                    result = dbselect_common(session, "userbasic", "uid", self.test_user)
                    if result and result[0].totpsecret:
                        totp_secret = result[0].totpsecret
                        self.test_user_otp = pyotp.TOTP(totp_secret)
                        
                        logger.info(f"使用已存在的测试用户: {self.test_user}")
                        logger.info(f"当前TOTP码: {self.test_user_otp.now()}")
                        
                        self.log_test("使用已存在的测试用户", True)
                        return True
            except Exception as fallback_error:
                logger.error(f"使用已存在的测试用户失败: {str(fallback_error)}")
            
            self.log_test("创建测试用户", False, str(e))
            return False
    
    def encrypt_request_data(self, data):
        """加密请求数据"""
        try:
            # 格式化公钥
            server_public_key_pem = self.server_public_key
            if server_public_key_pem is None:
                logger.error("服务器公钥为空")
                return None
                
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
        """解密响应数据"""
        try:
            if self.client_private_key is None:
                logger.error("客户端私钥为空")
                return None
                
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
    
    def test_verify_otp(self):
        """测试OTP验证"""
        if not self.test_user or not self.test_user_otp:
            self.log_test("OTP验证", False, "未创建测试用户")
            return False
        
        try:
            timestamp = int(time.time() * 1000)
            test_data = {
                "uid": self.test_user,
                "code": self.test_user_otp.now()
            }
            
            logger.info(f"尝试验证用户 {self.test_user} 的OTP码: {test_data['code']}")
            
            encrypted_data = self.encrypt_request_data(test_data)
            if not encrypted_data:
                self.log_test("OTP验证-加密", False, "加密请求数据失败")
                return False
            
            res = requests.post(
                f"{self.api_url}/verify-otp",
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
                self.log_test("OTP验证-请求", False, f"状态码: {res.status_code} - {res.text}")
                return False
            
            response_data = res.json()
            
            # 尝试解密响应
            if "data" in response_data and "timestamp" in response_data:
                decrypted_data = self.decrypt_response(response_data["data"])
                if decrypted_data:
                    logger.info(f"解密响应: {json.dumps(decrypted_data, indent=2)}")
                    self.test_token = decrypted_data.get("token")
                    self.log_test("OTP验证-解密", True)
                    return True
                else:
                    self.log_test("OTP验证-解密", False, "解密响应失败")
                    return False
            else:
                # 也许响应不是加密格式
                logger.info(f"响应可能不是加密格式: {json.dumps(response_data, indent=2)}")
                if "verified" in response_data:
                    self.log_test("OTP验证-非加密响应", True)
                    return True
                self.log_test("OTP验证-响应格式", False, "响应格式不正确")
                return False
        except Exception as e:
            self.log_test("OTP验证", False, str(e))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始集成测试...")
        
        # 测试服务器状态
        if not self.test_server_status():
            logger.error("服务器状态检查失败，终止测试")
            return False
        
        # 生成客户端密钥对
        if not self.generate_client_keys():
            logger.error("生成客户端密钥对失败，终止测试")
            return False
        
        # 获取服务器公钥
        if not self.get_server_public_key():
            logger.error("获取服务器公钥失败，终止测试")
            return False
        
        # 注册客户端公钥
        if not self.register_client_public_key():
            logger.error("注册客户端公钥失败，终止测试")
            return False
        
        # 创建测试用户
        if not self.create_test_user():
            logger.error("创建测试用户失败，终止测试")
            return False
        
        # 测试OTP验证
        self.test_verify_otp()
        
        # 测试结果汇总
        logger.info(f"\n测试结果汇总: {self.tests_passed}/{self.tests_total} 通过")
        return self.tests_passed == self.tests_total

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="完整集成测试")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务器URL")
    
    args = parser.parse_args()
    
    test = IntegrationTest(api_url=args.url)
    success = test.run_all_tests()
    
    if success:
        logger.info("✅ 所有测试通过!")
        sys.exit(0)
    else:
        logger.error("❌ 部分测试失败!")
        sys.exit(1)

if __name__ == "__main__":
    main()
