# doapi/main.py
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
import pyotp
from database import Session, dbselect_common
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from .auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from .authtotp import verify_totp as verify_totp_code
from .security import (
    decrypt_data,
    verify_security_headers,
    verify_signature,
    get_security_info
)
import json
import logging

# 配置更详细的日志记录
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log',  # 指定日志文件名
    filemode='w'  # 'w'表示覆盖模式，'a'表示追加模式
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    处理应用程序的启动和关闭事件
    """
    # 启动时的验证和初始化
    try:
        logger.info("Validating configuration...")
        required_env_vars = [
            "JWT_SECRET",
            "ENCRYPTION_KEY",
            "API_SECRET_KEY",
            "DATABASE_URL"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            error_msg = f"Missing required environment variables: {', '.join(missing_vars)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        # 验证安全配置
        from .security import get_encryption_key, get_api_secret, encrypt_data
        
        # 测试加密功能
        test_key = get_encryption_key()
        test_secret = get_api_secret()
        if not test_key or not test_secret:
            raise ValueError("Failed to initialize security keys")
            
        # 测试加密功能
        test_data = encrypt_data("test")
        logger.info("Successfully verified security configuration")
        
        # 验证数据库连接
        try:
            with Session() as session:
                session.connection()
            logger.info("Successfully verified database connection")
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise

    yield  # 应用运行时

    # 关闭时的清理工作
    logger.info("Shutting down application...")

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Secure API Backend",
    lifespan=lifespan
)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://192.168.1.18:3000"],  # 前端开发服务器地址
    allow_credentials=True,  # 允许携带认证信息（cookies等）
    allow_methods=["*"],    # 允许所有 HTTP 方法
    allow_headers=["*"],    # 允许所有 headers
)

class EncryptedRequest(BaseModel):
    data: str  # 加密后的数据

@app.get("/security-info")
async def security_info():
    """
    获取加密相关的公共信息
    """
    return get_security_info()

@app.post("/verify-otp")
async def verify_otp(
    request: EncryptedRequest,
    security_headers: dict = Depends(verify_security_headers)
):
    # 验证签名
    verify_signature(
        request.data,
        security_headers["timestamp"],
        security_headers["signature"]
    )
    
    # 解密数据
    try:
        decrypted_data = decrypt_data(request.data)
        data = json.loads(decrypted_data)
        if not isinstance(data, dict) or "code" not in data or "uid" not in data:
            raise HTTPException(status_code=400, detail="Invalid request data format")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to decrypt data")

    session = Session()
    try:
        # 使用解密后的数据进行验证
        result = dbselect_common(session, "userbasic", "uid", data["uid"])
        if not result:
            return {
                "verified": False,
                "message": "用户不存在"
            }

        user = result[0]
        if not user.totpsecret:
            return {
                "verified": False,
                "message": "未找到用户密钥"
            }

        # 使用 authtotp 模块验证 OTP
        if verify_totp_code(data["uid"], data["code"]):
            # 创建访问令牌
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.uid},
                expires_delta=access_token_expires
            )
            
            # 验证成功，返回用户信息和令牌
            return {
                "verified": True,
                "token": access_token,
                "user": {
                    "uid": user.uid,
                    "name": user.username if hasattr(user, 'username') else ""
                }
            }
        else:
            return {
                "verified": False,
                "message": "验证码错误"
            }
    finally:
        session.close()

@app.post("/tradingcommand")
async def trading_config(
    request: EncryptedRequest,
    security_headers: dict = Depends(verify_security_headers)
):
    """
    处理加密的交易命令
    """
    # 验证签名
    verify_signature(
        request.data,
        security_headers["timestamp"],
        security_headers["signature"]
    )
    
    # 解密数据
    try:
        decrypted_data = decrypt_data(request.data)
        trading_data = json.loads(decrypted_data)
        # TODO: 实现交易命令处理逻辑
        return {"message": "Trading command received", "data": trading_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Failed to process trading command")