# doapi/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pyotp
import os
from database import Session, dbselect_common
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from .auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from .authtotp import verify_totp as verify_totp_code

app = FastAPI()

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://192.168.1.18:3000"],  # 前端开发服务器地址
    allow_credentials=True,  # 允许携带认证信息（cookies等）
    allow_methods=["*"],    # 允许所有 HTTP 方法
    allow_headers=["*"],    # 允许所有 headers
)

class OTPRequest(BaseModel):
    code: str
    uid: str

@app.post("/verify-otp")
def verify_otp(data: OTPRequest):
    session = Session()
    try:
        # 使用 dbselect_common 查询用户的信息
        result = dbselect_common(session, "userbasic", "uid", data.uid)
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
        if verify_totp_code(data.uid, data.code):
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
