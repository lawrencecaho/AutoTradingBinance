# myfastapi/main.py
import sys
import os

# 添加项目根目录到Python路径
# 确保这在任何依赖于此路径的导入之前运行
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from pathlib import Path
from datetime import timedelta
import base64
import json
import time
from typing import Dict, Any, Optional
import logging
from fastapi import FastAPI, HTTPException, Depends, Header, status, APIRouter # Add APIRouter
from fastapi.middleware.cors import CORSMiddleware # Add CORSMiddleware
from sqlalchemy.orm import Session # Add Session
from database import dbselect_common, Session # Add dbselect_common and import Session from database.py

# 配置日志
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default_formatter": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s", # Simplified for console
            "use_colors": None,
        },
        "file_formatter": { # For our application file log
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console_handler": { # Uvicorn's console output
            "formatter": "default_formatter",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
        "app_file_handler": { # Our application log file
            "formatter": "file_formatter",
            "class": "logging.FileHandler",
            "filename": "fastapi.log", # Relative to where script is run
            "mode": "w",
        },
    },
    "loggers": {
        "uvicorn": { # Uvicorn's own operational logs
            "handlers": ["console_handler"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": { # Uvicorn's error logs (e.g., startup errors)
            "handlers": ["console_handler"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.access": { # Uvicorn's access logs (requests)
            "handlers": ["console_handler", "app_file_handler"], # Also send access logs to our file for completeness
            "level": "INFO",
            "propagate": False,
        },
        "myfastapi": { # Logger for the application modules
            "handlers": ["app_file_handler", "console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "__main__": { # Logger for main.py when run directly
            "handlers": ["app_file_handler", "console_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "root": { # Root logger configuration
        "handlers": ["app_file_handler"], # All uncaught logs go here
        "level": "DEBUG", # Set root logger level to DEBUG
    },
}

logger = logging.getLogger(__name__) # This will now use the '__main__' config from LOGGING_CONFIG

# 定义模型
from pydantic import BaseModel # Existing import
from contextlib import asynccontextmanager

# 定义模型
class EncryptedResponse(BaseModel): # MOVED & CORRECTED: Definition for EncryptedResponse
    data: str
    timestamp: int
    signature: str

class SecureRequest(BaseModel): # MOVED & CORRECTED: Definition for SecureRequest
    encrypted_data: str
    timestamp: int
    signature: Optional[str] = None

# 加密相关导入
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

# 项目内部导入
from myfastapi.auth import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, verify_token, get_current_user_from_token # MODIFIED: Added get_current_user_from_token
from myfastapi.authtotp import verify_totp as verify_totp_code
from myfastapi.security import (
    decrypt_data,
    encrypt_data,
    verify_security_headers,
    verify_signature,
    sign_data,
    get_security_info,
    PRIVATE_KEY,
    PUBLIC_KEY,
    store_client_public_key,
    get_client_public_key,
    encrypt_with_client_key,
    hybrid_encrypt_with_client_key
)
from myfastapi.chunked_encryption import chunk_encrypt_large_data
from myfastapi.echarts import router as echarts_router # 从 echarts 导入 router 并重命名以避免冲突

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """处理应用程序的启动和关闭事件"""
    try:
        logger.info("正在验证配置...")
        
        # 验证密钥管理系统
        try:
            from security import get_api_secret, get_jwt_secret
            api_secret = get_api_secret()
            jwt_secret = get_jwt_secret()
            if not api_secret or not jwt_secret:
                raise ValueError("密钥获取失败")
            logger.info("✅ 密钥管理系统验证成功")
        except Exception as e:
            error_msg = f"密钥管理系统验证失败: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # 验证数据库连接
        try:
            # 创建一个新的数据库会话
            session = Session()
            try:
                # 测试连接 - 使用engine直接连接测试
                from sqlalchemy import text
                session.execute(text("SELECT 1"))
                logger.info("数据库连接验证成功")
            finally:
                # 确保会话关闭
                session.close()
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

# 创建认证路由组
auth_router = APIRouter(prefix="/api/auth", tags=["authentication"])

# 工具函数
def encrypt_response(response_data: Dict[str, Any], client_id: Optional[str] = None) -> EncryptedResponse:
    """加密响应数据并生成签名"""
    current_timestamp = int(time.time() * 1000)
    
    try:
        json_data = json.dumps(response_data)
        data_size = len(json_data)
        logger.debug(f"原始响应数据大小: {data_size} 字节")
        
        # 加密方法选择策略
        encryption_strategy = "standard"
        if data_size > 1024 * 1024:  # 1MB以上使用分块加密
            encryption_strategy = "chunked"
            logger.debug(f"选择分块加密策略（数据大小: {data_size} 字节）")
        elif data_size > 200:  # 200字节以上使用混合加密
            encryption_strategy = "hybrid"
            logger.debug(f"选择混合加密策略（数据大小: {data_size} 字节）")
        else:
            logger.debug(f"选择标准RSA加密策略（数据大小: {data_size} 字节）")
        
        # 初始化变量
        encrypted_data = None
        encryption_methods_tried = []
        
        # 如果提供了客户端ID且有对应的公钥，使用客户端公钥加密
        client_public_key = None
        if client_id:
            logger.debug(f"尝试获取客户端 {client_id} 的公钥")
            client_public_key = get_client_public_key(client_id)
            
        if client_public_key:
            # 使用客户端公钥加密
            if encryption_strategy == "chunked":
                # 超大数据使用分块加密
                try:
                    logger.debug(f"数据大小 {data_size} 字节超过1MB，使用分块加密")
                    
                    # 计算合适的块大小：默认256KB，或数据大小的1/10（取较小值）
                    chunk_size = min(256 * 1024, data_size // 10)
                    if chunk_size < 10 * 1024:  # 至少10KB
                        chunk_size = 10 * 1024
                        
                    logger.debug(f"使用块大小: {chunk_size} 字节")
                    
                    # 使用分块加密
                    chunked_result = chunk_encrypt_large_data(json_data, client_public_key, chunk_size)
                    
                    # 检查分块加密是否成功
                    if chunked_result.get("success", False):
                        # 如果分块加密成功，返回结果
                        encrypted_data = json.dumps(chunked_result)
                        encryption_methods_tried.append("chunked_hybrid")
                        logger.info(f"使用分块加密成功处理超大数据响应 ({data_size} -> {len(encrypted_data)} 字节)")
                    else:
                        # 如果分块加密失败，记录错误
                        logger.error(f"分块加密失败: {chunked_result.get('error', '未知错误')}")
                        # 不设置encrypted_data，继续尝试其他方法
                except Exception as chunked_error:
                    logger.error(f"分块加密过程异常: {str(chunked_error)}")
                    # 继续尝试标准混合加密
            
            if encryption_strategy == "hybrid" or (encryption_strategy == "chunked" and encrypted_data is None):
                # 使用混合加密（AES+RSA）处理大数据
                try:
                    logger.debug(f"数据大小 {data_size} 字节超过RSA限制，使用混合加密")
                    
                    # 使用混合加密（AES+RSA）
                    hybrid_result = hybrid_encrypt_with_client_key(json_data, client_public_key)
                    
                    # 检查混合加密是否成功
                    if hybrid_result.get("success", False):
                        # 如果混合加密成功，返回结果
                        encrypted_data = json.dumps(hybrid_result)
                        encryption_methods_tried.append("hybrid")
                        logger.info(f"使用混合加密成功处理大数据响应 ({data_size} -> {len(encrypted_data)} 字节)")
                    else:
                        # 如果混合加密失败，记录错误
                        logger.error(f"混合加密失败: {hybrid_result.get('error', '未知错误')}")
                        # 不设置encrypted_data，继续尝试其他方法
                except Exception as hybrid_error:
                    logger.error(f"混合加密过程异常: {str(hybrid_error)}")
                    # 继续尝试其他方法
            
            # 如果分块加密和混合加密都失败或数据较小，尝试直接RSA加密
            if encrypted_data is None:
                try:
                    logger.debug(f"尝试使用客户端公钥直接RSA加密 (数据大小: {data_size} 字节)")
                    encrypted_data = encrypt_with_client_key(json_data, client_public_key)
                    encryption_methods_tried.append("client_rsa")
                    logger.info(f"使用客户端 {client_id} 的公钥RSA加密响应成功")
                except Exception as client_encrypt_error:
                    logger.error(f"使用客户端公钥加密失败: {str(client_encrypt_error)}")
                    # 继续尝试服务器标准加密
        
        # 如果客户端加密方法都失败，使用服务器的标准加密
        if encrypted_data is None:
            try:
                logger.debug("使用服务器标准加密")
                encrypted_data = encrypt_data(json_data)
                encryption_methods_tried.append("server_rsa")
                logger.info("使用服务器标准加密成功")
            except Exception as server_encrypt_error:
                logger.error(f"服务器标准加密失败: {str(server_encrypt_error)}")
                # 所有加密方法都失败，发送明文错误信息
                fallback_data = {
                    "error": "encryption_failed",
                    "message": "无法加密响应数据，服务器内部错误",
                    "timestamp": current_timestamp
                }
                encrypted_data = json.dumps(fallback_data)
                encryption_methods_tried.append("plaintext_fallback")
                logger.critical("所有加密方法均失败，返回明文错误信息")
        
        # 记录最终使用的加密方法
        logger.info(f"响应加密完成，使用方法: {', '.join(encryption_methods_tried)}")
        
        # 生成签名
        try:
            signature = sign_data(encrypted_data, str(current_timestamp))
        except Exception as sign_error:
            logger.error(f"签名生成失败: {str(sign_error)}")
            signature = "signature_error"
        
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

@auth_router.post("/verify-otp")
async def verify_otp(
    request: SecureRequest,
    security_headers: dict = Depends(verify_security_headers)
):
    """验证OTP"""
    # 验证签名 - 现在处理前端固定签名值
    if not verify_signature(
        request.encrypted_data,
        str(request.timestamp),
        request.signature or "frontend"
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # 解密并验证数据
    try:
        data = await decrypt_request_data(request)
        if not isinstance(data, dict) or "code" not in data or "uid" not in data:
            raise HTTPException(status_code=400, detail="无效的请求数据格式")
        
        # 获取客户端ID，用于后续响应加密
        client_id = security_headers.get("api_key")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 创建一个数据库会话
    session = Session()
    try:
        # 验证用户
        result = dbselect_common(session, "userbasic", "uid", data["uid"])
        if not result:
            return encrypt_response({
                "verified": False,
                "message": "用户不存在"
            }, client_id)

        user = result[0]
        if not user.totpsecret:
            return encrypt_response({
                "verified": False,
                "message": "未找到用户密钥"
            }, client_id)

        # 验证OTP
        if verify_totp_code(data["uid"], data["code"]):
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.uid},
                expires_delta=access_token_expires
            )
            
            # 生成 refresh token
            from auth import create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS
            refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            refresh_token = create_refresh_token(
                data={"sub": user.uid},
                expires_delta=refresh_token_expires
            )
            
            return encrypt_response({
                "verified": True,
                "token": access_token,
                "user": {
                    "uid": user.uid,
                    "name": user.username if hasattr(user, 'username') else ""
                },
                "expiresIn": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 转换为秒
                "refreshToken": refresh_token
            }, client_id)
        else:
            return encrypt_response({
                "verified": False,
                "message": "验证码错误"
            }, client_id)
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
        # 获取客户端ID，用于后续响应加密
        client_id = security_headers.get("api_key")
        trading_data = await decrypt_request_data(request)
        return encrypt_response({
            "message": "已接收交易命令",
            "data": trading_data
        }, client_id)
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

@app.post("/register-client-key")
async def register_client_key(request: dict):
    """注册客户端公钥"""
    if "client_id" not in request or "public_key" not in request:
        raise HTTPException(status_code=400, detail="Missing client_id or public_key")
    
    try:
        store_client_public_key(request["client_id"], request["public_key"])
        return {"status": "success", "message": "Client public key registered"}
    except Exception as e:
        logger.error(f"注册客户端公钥失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
# 刷新访问令牌
@auth_router.post("/refresh")
async def refresh_token(
    security_headers: dict = Depends(verify_security_headers),
    authorization: str = Header(None)
):
    """刷新访问令牌"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查令牌格式
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证方案无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        # 验证 refresh token
        from auth import verify_refresh_token, create_access_token, create_refresh_token, REFRESH_TOKEN_EXPIRE_DAYS
        payload = verify_refresh_token(token)
        
        # 获取用户ID
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # 创建新的 access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=access_token_expires
        )
        
        # 创建新的 refresh token
        refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        new_refresh_token = create_refresh_token(
            data={"sub": user_id},
            expires_delta=refresh_token_expires
        )
        
        # 获取客户端ID用于响应加密
        client_id = security_headers.get("api_key")
        
        # 统一响应格式，符合文档要求
        return encrypt_response({
            "access_token": new_access_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # 转换为秒
            "refresh_token": new_refresh_token
        }, client_id)
        
    except HTTPException as e:
        # 重新抛出 HTTPException
        raise e
    except Exception as e:
        logger.error(f"刷新令牌失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌失败"
        )

@auth_router.get("/check-session")
async def check_session(
    security_headers: dict = Depends(verify_security_headers),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """检查会话状态"""
    try:
        # 获取客户端ID用于响应加密
        client_id = security_headers.get("api_key")
        
        # 获取用户ID
        user_id = current_user.get("sub")
        if not user_id:
            return encrypt_response({
                "valid": False,
                "message": "无效的用户令牌"
            }, client_id)
        
        # 创建数据库会话查询用户信息
        session = Session()
        try:
            # 验证用户是否存在
            result = dbselect_common(session, "userbasic", "uid", user_id)
            if not result:
                return encrypt_response({
                    "valid": False,
                    "message": "用户不存在"
                }, client_id)
            
            user = result[0]
            
            # 返回会话有效信息
            return encrypt_response({
                "valid": True,
                "user": {
                    "uid": user.uid,
                    "name": user.username if hasattr(user, 'username') else "",
                    "roles": ["user"]  # 默认角色，可根据需要扩展
                }
            }, client_id)
            
        finally:
            session.close()
            
    except HTTPException as e:
        # 处理JWT验证失败等情况
        client_id = security_headers.get("api_key")
        return encrypt_response({
            "valid": False,
            "message": "会话已过期或无效"
        }, client_id)
    except Exception as e:
        logger.error(f"会话检查失败: {str(e)}")
        client_id = security_headers.get("api_key")
        return encrypt_response({
            "valid": False,
            "message": "服务器内部错误"
        }, client_id)

@auth_router.post("/logout")
async def logout(
    security_headers: dict = Depends(verify_security_headers),
    current_user: Dict[str, Any] = Depends(get_current_user_from_token)
):
    """用户登出"""
    try:
        # 获取客户端ID用于响应加密
        client_id = security_headers.get("api_key")
        
        # 获取用户ID
        user_id = current_user.get("sub")
        if not user_id:
            return encrypt_response({
                "success": False,
                "message": "无效的用户令牌"
            }, client_id)
        
        # 记录登出日志
        logger.info(f"用户登出: user_id={user_id}, ip={security_headers.get('x-forwarded-for', 'unknown')}")
        
        # 返回成功响应
        # 注意：由于当前没有实现Token黑名单，这里主要是标记登出成功
        # 实际的Token失效需要前端删除本地存储的Token
        return encrypt_response({
            "success": True,
            "message": "已成功登出"
        }, client_id)
        
    except HTTPException as e:
        # 处理JWT验证失败等情况
        client_id = security_headers.get("api_key")
        return encrypt_response({
            "success": False,
            "message": "登出失败：会话无效"
        }, client_id)
    except Exception as e:
        logger.error(f"登出失败: {str(e)}")
        client_id = security_headers.get("api_key")
        return encrypt_response({
            "success": False,
            "message": "登出失败：服务器内部错误"
        }, client_id)

app.include_router(echarts_router, prefix="/echarts") # 您可以为这些路由添加一个前缀，例如 /echarts

# 注册认证路由组
app.include_router(auth_router)

# 向后兼容路由 - 简单重定向提示
@app.post("/verify-otp")
async def verify_otp_legacy():
    """向后兼容提示 - 请使用新路径"""
    logger.warning("访问了已弃用的 /verify-otp 路径")
    raise HTTPException(
        status_code=301, 
        detail="此接口已迁移到 /api/auth/verify-otp，请更新API调用路径"
    )

@app.post("/refresh-token") 
async def refresh_token_legacy():
    """向后兼容提示 - 请使用新路径"""
    logger.warning("访问了已弃用的 /refresh-token 路径")
    raise HTTPException(
        status_code=301, 
        detail="此接口已迁移到 /api/auth/refresh，请更新API调用路径"
    )

# 启动API模块
if __name__ == "__main__":
    import uvicorn
    logger.info("启动 FastAPI 服务器...")
    uvicorn.run(
        "myfastapi.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=LOGGING_CONFIG
    )