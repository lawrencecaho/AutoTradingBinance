# myfastapi/queue.py
"""
队列配置管理API
提供队列的CRUD操作，支持混合加密
"""
import os
import sys
import json
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from fastapi import APIRouter, HTTPException, Depends, Header, Request, Response
from pydantic import BaseModel, Field

# 导入加密模块
from myfastapi.security import (
    decrypt_data,
    encrypt_data,
    verify_security_headers,
    verify_signature,
    get_client_public_key,
    hybrid_encrypt_with_client_key
)

# 导入数据库操作
from DatabaseOperator.pg_operator import fetcher_queue_manager

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/queue", tags=["队列管理"])

# Pydantic 模型定义
class SecureRequest(BaseModel):
    encrypted_data: str
    timestamp: int
    signature: Optional[str] = None

class QueueConfigCreate(BaseModel):
    queue_name: str = Field(..., description="队列名称", min_length=1, max_length=255)
    symbol: str = Field(..., description="交易对符号", min_length=1, max_length=50)
    interval: str = Field(..., description="K线周期", min_length=1, max_length=10)
    exchange: str = Field(default="binance", description="交易所名称", max_length=50)
    description: Optional[str] = Field(None, description="队列描述", max_length=500)
    # 注意：created_by 字段不在此模型中，由API自动获取

class QueueConfigUpdate(BaseModel):
    queue_name: Optional[str] = Field(None, description="队列名称", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="队列描述", max_length=500)

# 工具函数
def encrypt_response(response_data: Dict[str, Any], client_id: Optional[str] = None) -> str:
    """加密响应数据，参考main.py的实现"""
    try:
        json_data = json.dumps(response_data)
        data_size = len(json_data)
        
        # 获取客户端公钥
        client_public_key = None
        if client_id:
            client_public_key = get_client_public_key(client_id)
        
        if client_public_key and data_size > 200:
            # 使用混合加密
            result = hybrid_encrypt_with_client_key(json_data, client_public_key)
            if result.get("success"):
                return json.dumps({
                    "encrypted_data": result.get("encrypted_data"),
                    "encrypted_key": result.get("encrypted_key"),
                    "encryption_method": result.get("encryption_method")
                })
        
        # 回退到标准加密
        encrypted_data = encrypt_data(json_data)
        current_timestamp = int(time.time() * 1000)
        signature = "server_generated"  # 简化签名处理
        
        return json.dumps({
            "encrypted_data": encrypted_data,
            "timestamp": current_timestamp,
            "signature": signature
        })
        
    except Exception as e:
        logger.error(f"响应加密失败: {e}")
        # 应急情况下返回未加密数据
        return json.dumps(response_data)

async def decrypt_request_data(request: SecureRequest) -> Dict[str, Any]:
    """解密请求数据，参考main.py的实现"""
    current_time = int(time.time() * 1000)
    if current_time - request.timestamp > 60000:
        raise HTTPException(status_code=401, detail="请求已过期")
    
    try:
        return json.loads(decrypt_data(request.encrypted_data))
    except Exception as e:
        logger.error(f"请求解密失败: {e}")
        raise HTTPException(status_code=400, detail=f"解密失败: {str(e)}")

# API 端点

@router.get("/edfqs/list", summary="获取所有队列配置")
async def get_all_queues(
    active_only: bool = True,
    security_headers: dict = Depends(verify_security_headers)
) -> Response:
    """
    获取所有队列配置列表
    
    Args:
        active_only: 是否只返回激活的队列，默认为True
    
    Returns:
        加密的队列配置列表
    """
    try:
        configs = fetcher_queue_manager.get_all_queue_configs(active_only=active_only)
        
        response_data = {
            "success": True,
            "data": configs,
            "total": len(configs),
            "message": "获取队列配置成功"
        }
        
        # 加密响应
        client_id = security_headers.get("api_key")
        encrypted_response = encrypt_response(response_data, client_id)
        
        return Response(
            content=encrypted_response,
            media_type="application/json",
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logger.error(f"获取队列配置失败: {e}")
        error_response = {
            "success": False,
            "message": f"获取队列配置失败: {str(e)}"
        }
        client_id = security_headers.get("api_key") if 'security_headers' in locals() else None
        encrypted_error = encrypt_response(error_response, client_id)
        
        return Response(
            content=encrypted_error,
            media_type="application/json",
            status_code=500
        )

@router.get("/edfqs/{queue_name}", summary="获取特定队列配置")
async def get_queue_config(
    queue_name: str,
    security_headers: dict = Depends(verify_security_headers)
) -> Response:
    """
    获取指定队列的配置信息
    
    Args:
        queue_name: 队列名称
    
    Returns:
        加密的队列配置信息
    """
    try:
        config = fetcher_queue_manager.get_queue_config(queue_name)
        
        if not config:
            response_data = {
                "success": False,
                "message": f"队列配置不存在: {queue_name}"
            }
            client_id = security_headers.get("api_key")
            encrypted_response = encrypt_response(response_data, client_id)
            
            return Response(
                content=encrypted_response,
                media_type="application/json",
                status_code=404
            )
        
        response_data = {
            "success": True,
            "data": config,
            "message": "获取队列配置成功"
        }
        
        client_id = security_headers.get("api_key")
        encrypted_response = encrypt_response(response_data, client_id)
        
        return Response(
            content=encrypted_response,
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"获取队列配置失败: {e}")
        error_response = {
            "success": False,
            "message": f"获取队列配置失败: {str(e)}"
        }
        client_id = security_headers.get("api_key") if 'security_headers' in locals() else None
        encrypted_error = encrypt_response(error_response, client_id)
        
        return Response(
            content=encrypted_error,
            media_type="application/json",
            status_code=500
        )

@router.post("/edfqs/create", summary="创建新队列配置")
async def create_queue_config(
    request: SecureRequest,
    security_headers: dict = Depends(verify_security_headers)
) -> Response:
    """
    创建新的队列配置
    
    请求体应包含队列配置信息（加密）
    """
    try:
        # 验证签名
        if not verify_signature(
            request.encrypted_data,
            str(request.timestamp),
            request.signature or "frontend"
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # 解密请求数据
        request_data = await decrypt_request_data(request)
        
        # 验证请求数据
        if not request_data:
            raise HTTPException(status_code=400, detail="缺少请求数据")
        
        # 创建队列配置对象进行验证
        try:
            queue_config = QueueConfigCreate(**request_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"请求数据格式错误: {str(e)}")
        
        # 检查队列名称是否已存在
        existing_config = fetcher_queue_manager.get_queue_config(queue_config.queue_name)
        if existing_config:
            response_data = {
                "success": False,
                "message": f"队列名称已存在: {queue_config.queue_name}"
            }
            client_id = security_headers.get("api_key")
            encrypted_response = encrypt_response(response_data, client_id)
            
            return Response(
                content=encrypted_response,
                media_type="application/json",
                status_code=400
            )
        
        # 从安全头部获取创建者信息
        created_by = security_headers.get("api_key", "unknown_user")
        
        # 创建队列配置
        result = fetcher_queue_manager.create_queue_config(
            queue_name=queue_config.queue_name,
            symbol=queue_config.symbol,
            interval=queue_config.interval,
            exchange=queue_config.exchange,
            description=queue_config.description,
            created_by=created_by
        )
        
        if result:
            # 获取创建的配置信息
            created_config = fetcher_queue_manager.get_queue_config(queue_config.queue_name)
            response_data = {
                "success": True,
                "data": created_config,
                "message": "队列配置创建成功"
            }
            status_code = 201
        else:
            response_data = {
                "success": False,
                "message": "队列配置创建失败"
            }
            status_code = 500
        
        client_id = security_headers.get("api_key")
        encrypted_response = encrypt_response(response_data, client_id)
        
        return Response(
            content=encrypted_response,
            media_type="application/json",
            status_code=status_code
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建队列配置失败: {e}")
        error_response = {
            "success": False,
            "message": f"创建队列配置失败: {str(e)}"
        }
        client_id = security_headers.get("api_key") if 'security_headers' in locals() else None
        encrypted_error = encrypt_response(error_response, client_id)
        
        return Response(
            content=encrypted_error,
            media_type="application/json",
            status_code=500
        )

@router.put("/edfqs/{queue_name}", summary="更新队列配置")
async def update_queue_config(
    queue_name: str,
    request: SecureRequest,
    security_headers: dict = Depends(verify_security_headers)
) -> Response:
    """
    更新队列配置
    
    激活状态的队列只能修改队列名称和描述，不能修改核心字段
    """
    try:
        # 验证签名
        if not verify_signature(
            request.encrypted_data,
            str(request.timestamp),
            request.signature or "frontend"
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # 解密请求数据
        request_data = await decrypt_request_data(request)
        
        # 验证请求数据
        if not request_data:
            raise HTTPException(status_code=400, detail="缺少请求数据")
        
        # 检查队列是否存在
        existing_config = fetcher_queue_manager.get_queue_config(queue_name)
        if not existing_config:
            response_data = {
                "success": False,
                "message": f"队列配置不存在: {queue_name}"
            }
            client_id = security_headers.get("api_key")
            encrypted_response = encrypt_response(response_data, client_id)
            
            return Response(
                content=encrypted_response,
                media_type="application/json",
                status_code=404
            )
        
        # 检查队列是否激活
        is_active = existing_config.get('is_active') == True
        
        # 验证更新数据
        allowed_fields = ['queue_name', 'description']
        if not is_active:
            # 非激活状态可以修改所有字段（除了核心不可变字段）
            allowed_fields.extend(['symbol', 'interval', 'exchange'])
        
        # 过滤只允许的字段
        update_data = {k: v for k, v in request_data.items() if k in allowed_fields and v is not None}
        
        if not update_data:
            response_data = {
                "success": False,
                "message": "没有可更新的字段" + (f"（激活状态的队列只能修改: {', '.join(['队列名称', '描述'])}）" if is_active else "")
            }
            client_id = security_headers.get("api_key")
            encrypted_response = encrypt_response(response_data, client_id)
            
            return Response(
                content=encrypted_response,
                media_type="application/json",
                status_code=400
            )
        
        # 如果要更新队列名称，检查新名称是否已存在
        if 'queue_name' in update_data and update_data['queue_name'] != queue_name:
            new_queue_name = update_data['queue_name']
            existing_new_config = fetcher_queue_manager.get_queue_config(new_queue_name)
            if existing_new_config:
                response_data = {
                    "success": False,
                    "message": f"新队列名称已存在: {new_queue_name}"
                }
                client_id = security_headers.get("api_key")
                encrypted_response = encrypt_response(response_data, client_id)
                
                return Response(
                    content=encrypted_response,
                    media_type="application/json",
                    status_code=400
                )
        
        # 从安全头部获取更新者信息
        updated_by = security_headers.get("api_key", "unknown_user")
        
        # 执行更新
        result = fetcher_queue_manager.update_queue_config(queue_name, updated_by=updated_by, **update_data)
        
        if result:
            # 获取更新后的配置
            # 如果队列名称被更新，使用新名称查询
            final_queue_name = update_data.get('queue_name', queue_name)
            updated_config = fetcher_queue_manager.get_queue_config(final_queue_name)
            
            response_data = {
                "success": True,
                "data": updated_config,
                "message": "队列配置更新成功"
            }
        else:
            response_data = {
                "success": False,
                "message": "队列配置更新失败"
            }
        
        client_id = security_headers.get("api_key")
        encrypted_response = encrypt_response(response_data, client_id)
        
        return Response(
            content=encrypted_response,
            media_type="application/json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新队列配置失败: {e}")
        error_response = {
            "success": False,
            "message": f"更新队列配置失败: {str(e)}"
        }
        client_id = security_headers.get("api_key") if 'security_headers' in locals() else None
        encrypted_error = encrypt_response(error_response, client_id)
        
        return Response(
            content=encrypted_error,
            media_type="application/json",
            status_code=500
        )

@router.post("/edfqs/{queue_name}/activate", summary="激活队列")
async def activate_queue(
    queue_name: str,
    security_headers: dict = Depends(verify_security_headers)
) -> Response:
    """
    激活指定队列
    """
    try:
        # 检查队列是否存在
        existing_config = fetcher_queue_manager.get_queue_config(queue_name)
        if not existing_config:
            response_data = {
                "success": False,
                "message": f"队列配置不存在: {queue_name}"
            }
            client_id = security_headers.get("api_key")
            encrypted_response = encrypt_response(response_data, client_id)
            
            return Response(
                content=encrypted_response,
                media_type="application/json",
                status_code=404
            )
        
        # 从安全头部获取操作者信息
        updated_by = security_headers.get("api_key", "unknown_user")
        
        # 激活队列
        result = fetcher_queue_manager.activate_queue(queue_name, updated_by=updated_by)
        
        if result:
            updated_config = fetcher_queue_manager.get_queue_config(queue_name)
            response_data = {
                "success": True,
                "data": updated_config,
                "message": f"队列 {queue_name} 激活成功"
            }
        else:
            response_data = {
                "success": False,
                "message": f"队列 {queue_name} 激活失败"
            }
        
        client_id = security_headers.get("api_key")
        encrypted_response = encrypt_response(response_data, client_id)
        
        return Response(
            content=encrypted_response,
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"激活队列失败: {e}")
        error_response = {
            "success": False,
            "message": f"激活队列失败: {str(e)}"
        }
        client_id = security_headers.get("api_key") if 'security_headers' in locals() else None
        encrypted_error = encrypt_response(error_response, client_id)
        
        return Response(
            content=encrypted_error,
            media_type="application/json",
            status_code=500
        )

@router.post("/edfqs/{queue_name}/deactivate", summary="停用队列")
async def deactivate_queue(
    queue_name: str,
    security_headers: dict = Depends(verify_security_headers)
) -> Response:
    """
    停用指定队列
    """
    try:
        # 检查队列是否存在
        existing_config = fetcher_queue_manager.get_queue_config(queue_name)
        if not existing_config:
            response_data = {
                "success": False,
                "message": f"队列配置不存在: {queue_name}"
            }
            client_id = security_headers.get("api_key")
            encrypted_response = encrypt_response(response_data, client_id)
            
            return Response(
                content=encrypted_response,
                media_type="application/json",
                status_code=404
            )
        
        # 从安全头部获取操作者信息
        updated_by = security_headers.get("api_key", "unknown_user")
        
        # 停用队列
        result = fetcher_queue_manager.deactivate_queue(queue_name, updated_by=updated_by)
        
        if result:
            updated_config = fetcher_queue_manager.get_queue_config(queue_name)
            response_data = {
                "success": True,
                "data": updated_config,
                "message": f"队列 {queue_name} 停用成功"
            }
        else:
            response_data = {
                "success": False,
                "message": f"队列 {queue_name} 停用失败"
            }
        
        client_id = security_headers.get("api_key")
        encrypted_response = encrypt_response(response_data, client_id)
        
        return Response(
            content=encrypted_response,
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"停用队列失败: {e}")
        error_response = {
            "success": False,
            "message": f"停用队列失败: {str(e)}"
        }
        client_id = security_headers.get("api_key") if 'security_headers' in locals() else None
        encrypted_error = encrypt_response(error_response, client_id)
        
        return Response(
            content=encrypted_error,
            media_type="application/json",
            status_code=500
        )

@router.delete("/edfqs/{queue_name}/delete", summary="删除队列配置")
async def delete_queue_config(
    queue_name: str,
    security_headers: dict = Depends(verify_security_headers)
) -> Response:
    """
    删除指定队列配置
    
    出于安全考虑，激活状态的队列不能直接删除
    """
    try:
        # 检查队列是否存在
        existing_config = fetcher_queue_manager.get_queue_config(queue_name)
        if not existing_config:
            response_data = {
                "success": False,
                "message": f"队列配置不存在: {queue_name}"
            }
            client_id = security_headers.get("api_key")
            encrypted_response = encrypt_response(response_data, client_id)
            
            return Response(
                content=encrypted_response,
                media_type="application/json",
                status_code=404
            )
        
        # 检查队列是否激活
        is_active = existing_config.get('is_active') == True
        if is_active:
            response_data = {
                "success": False,
                "message": f"激活状态的队列不能删除，请先停用队列: {queue_name}"
            }
            client_id = security_headers.get("api_key")
            encrypted_response = encrypt_response(response_data, client_id)
            
            return Response(
                content=encrypted_response,
                media_type="application/json",
                status_code=400
            )
        
        # 删除队列
        result = fetcher_queue_manager.delete_queue_config(queue_name)
        
        if result:
            response_data = {
                "success": True,
                "message": f"队列 {queue_name} 删除成功"
            }
        else:
            response_data = {
                "success": False,
                "message": f"队列 {queue_name} 删除失败"
            }
        
        client_id = security_headers.get("api_key")
        encrypted_response = encrypt_response(response_data, client_id)
        
        return Response(
            content=encrypted_response,
            media_type="application/json"
        )
        
    except Exception as e:
        logger.error(f"删除队列失败: {e}")
        error_response = {
            "success": False,
            "message": f"删除队列失败: {str(e)}"
        }
        client_id = security_headers.get("api_key") if 'security_headers' in locals() else None
        encrypted_error = encrypt_response(error_response, client_id)
        
        return Response(
            content=encrypted_error,
            media_type="application/json",
            status_code=500
        )

# 订单队列接口
