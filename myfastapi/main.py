# myfastapi/main.py
import sys
import os
from pathlib import Path
from datetime import timedelta
import base64
import json
import time
from typing import Dict, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='fastapi.log',
    filemode='w'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# FastAPI相关导入
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# 加密相关导入
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

# 项目内部导入
from myfastapi.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from myfastapi.authtotp import verify_totp as verify_totp_code
from myfastapi.security import (
    decrypt_data,
    encrypt_data,
    verify_security_headers,
    verify_signature,
    sign_data,
    get_security_info,
    PRIVATE_KEY,
    PUBLIC_KEY
)
from database import Session, dbselect_common

# 定义模型
class SecureRequest(BaseModel):
    encrypted_data: str
    timestamp: int
    signature: str | None = None

class EncryptedResponse(BaseModel):
    data: str
    timestamp: int
    signature: str

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """处理应用程序的启动和关闭事件"""
    try:
        logger.info("正在验证配置...")
        required_env_vars = [
            "JWT_SECRET",
            "API_SECRET_KEY",
            "DATABASE_URL"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            error_msg = f"缺少必要的环境变量: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 验证数据库连接
        try:
            with Session() as session:
                session.connection()
            logger.info("数据库连接验证成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {str(e)}")
            raise
        
    except Exception as e:
        logger.error(f"配置验证失败: {str(e)}")
        raise

    yield

    logger.info("应用程序关闭中...")

# 创建FastAPI应用实例
app = FastAPI(
    title="安全API后端",
    description="加密通信API后端",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 工具函数
def encrypt_response(response_data: Dict[str, Any]) -> EncryptedResponse:
    """加密响应数据并生成签名"""
    current_timestamp = int(time.time() * 1000)
    
    try:
        json_data = json.dumps(response_data)
        encrypted_data = encrypt_data(json_data)
        signature = sign_data(encrypted_data, str(current_timestamp))
        
        return EncryptedResponse(
            data=encrypted_data,
            timestamp=current_timestamp,
            signature=signature
        )
    except Exception as e:
        logger.error(f"加密响应失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加密响应失败: {str(e)}")

async def decrypt_request_data(request: SecureRequest) -> Dict[str, Any]:
    """解密请求数据"""
    current_time = int(time.time() * 1000)
    if current_time - request.timestamp > 60000:
        raise HTTPException(status_code=401, detail="请求已过期")
    
    try:
        return json.loads(decrypt_data(request.encrypted_data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解密失败: {str(e)}")

# API端点
@app.get("/security-info")
async def security_info():
    """获取加密相关的公共信息"""
    return get_security_info()

@app.post("/verify-otp")
async def verify_otp(
    request: SecureRequest,
    security_headers: dict = Depends(verify_security_headers)
):
    """验证OTP"""
    # 验证签名
    verify_signature(
        request.encrypted_data,
        str(request.timestamp),
        request.signature or ""
    )
    
    # 解密并验证数据
    try:
        data = await decrypt_request_data(request)
        if not isinstance(data, dict) or "code" not in data or "uid" not in data:
            raise HTTPException(status_code=400, detail="无效的请求数据格式")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    session = Session()
    try:
        # 验证用户
        result = dbselect_common(session, "userbasic", "uid", data["uid"])
        if not result:
            return encrypt_response({
                "verified": False,
                "message": "用户不存在"
            })

        user = result[0]
        if not user.totpsecret:
            return encrypt_response({
                "verified": False,
                "message": "未找到用户密钥"
            })

        # 验证OTP
        if verify_totp_code(data["uid"], data["code"]):
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.uid},
                expires_delta=access_token_expires
            )
            
            return encrypt_response({
                "verified": True,
                "token": access_token,
                "user": {
                    "uid": user.uid,
                    "name": user.username if hasattr(user, 'username') else ""
                }
            })
        else:
            return encrypt_response({
                "verified": False,
                "message": "验证码错误"
            })
    finally:
        session.close()

@app.post("/tradingcommand")
async def trading_config(
    request: SecureRequest,
    security_headers: dict = Depends(verify_security_headers)
):
    """处理加密的交易命令"""
    verify_signature(
        request.encrypted_data,
        str(request.timestamp),
        request.signature or ""
    )
    
    try:
        trading_data = await decrypt_request_data(request)
        return encrypt_response({
            "message": "已接收交易命令",
            "data": trading_data
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"处理交易命令失败: {str(e)}")

@app.post("/api/hybrid-encrypt")
async def get_temporary_key():
    """获取临时AES密钥，使用RSA加密传输"""
    try:
        aes_key = os.urandom(32)
        
        if not isinstance(PUBLIC_KEY, rsa.RSAPublicKey):
            raise ValueError("公钥类型不正确")
            
        padding_algorithm = padding.OAEP(
            mgf=padding.MGF1(hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
        encrypted_key = PUBLIC_KEY.encrypt(aes_key, padding_algorithm)
        
        return {
            "encrypted_key": base64.b64encode(encrypted_key).decode('utf-8'),
            "timestamp": int(time.time() * 1000)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成临时密钥失败: {str(e)}")

# 启动服务器
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)