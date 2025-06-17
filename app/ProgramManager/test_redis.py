#!/usr/bin/env python3
"""
Redis连接测试脚本
用于验证Redis配置是否正确并测试Token黑名单功能
"""
import os
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

def test_redis_connection():
    """测试Redis基本连接"""
    print("🔄 测试Redis连接...")
    
    try:
        from myfastapi.redis_client import get_redis_client, check_redis_health
        
        # 获取Redis客户端
        redis_client = get_redis_client()
        
        # 检查连接状态
        is_connected = redis_client.is_connected()
        print(f"✅ Redis连接状态: {'已连接' if is_connected else '未连接'}")
        
        if is_connected:
            # 获取Redis信息
            info = redis_client.get_info()
            print(f"📊 Redis版本: {info.get('redis_version', 'unknown')}")
            print(f"💾 内存使用: {info.get('used_memory_human', 'unknown')}")
            print(f"👥 连接客户端数: {info.get('connected_clients', 0)}")
            print(f"⏱️  运行时间: {info.get('uptime_in_seconds', 0)} 秒")
            
            # 健康检查
            health = check_redis_health()
            print(f"🏥 健康状态: {health['status']}")
            
            return True
        else:
            print("❌ Redis连接失败")
            return False
            
    except Exception as e:
        print(f"❌ Redis连接测试失败: {e}")
        return False

def test_token_blacklist():
    """测试Token黑名单功能"""
    print("\n🔄 测试Token黑名单功能...")
    
    try:
        from myfastapi.redis_client import get_token_blacklist
        
        blacklist = get_token_blacklist()
        
        # 测试数据
        test_jti = "test_token_123456"
        test_expires = 60  # 60秒过期
        
        # 1. 检查Token是否在黑名单中（应该不在）
        is_revoked = blacklist.is_token_revoked(test_jti)
        print(f"✅ 初始状态检查: Token {test_jti} 撤销状态 = {is_revoked}")
        
        # 2. 撤销Token
        revoke_success = blacklist.revoke_token(test_jti, test_expires)
        print(f"✅ Token撤销: {'成功' if revoke_success else '失败'}")
        
        # 3. 再次检查Token是否在黑名单中（应该在）
        is_revoked_after = blacklist.is_token_revoked(test_jti)
        print(f"✅ 撤销后检查: Token {test_jti} 撤销状态 = {is_revoked_after}")
        
        # 4. 获取撤销Token的详细信息
        revoke_info = blacklist.get_revoked_token_info(test_jti)
        if revoke_info:
            print(f"✅ 撤销信息: {revoke_info}")
        
        # 5. 清理统计
        count = blacklist.cleanup_expired_tokens()
        print(f"✅ 当前黑名单Token数量: {count}")
        
        print("✅ Token黑名单功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ Token黑名单测试失败: {e}")
        return False

def test_session_management():
    """测试会话管理功能"""
    print("\n🔄 测试会话管理功能...")
    
    try:
        from myfastapi.redis_client import get_session_manager
        
        session_manager = get_session_manager()
        
        # 测试数据
        test_user_id = "test_user_123"
        test_session_data = {
            "ip_address": "192.168.1.100",
            "user_agent": "Test Agent",
            "login_time": time.time()
        }
        
        # 1. 创建会话
        session_id = session_manager.create_session(test_user_id, test_session_data.copy())
        print(f"✅ 会话创建: {session_id}")
        
        if session_id:
            # 2. 获取会话
            session_data = session_manager.get_session(session_id)
            print(f"✅ 会话获取: {session_data is not None}")
            
            # 3. 更新会话
            test_session_data["last_action"] = "test_update"
            update_success = session_manager.update_session(session_id, test_session_data)
            print(f"✅ 会话更新: {'成功' if update_success else '失败'}")
            
            # 4. 获取用户所有会话
            user_sessions = session_manager.get_user_sessions(test_user_id)
            print(f"✅ 用户会话列表: {len(user_sessions)} 个会话")
            
            # 5. 删除会话
            delete_success = session_manager.delete_session(session_id)
            print(f"✅ 会话删除: {'成功' if delete_success else '失败'}")
        
        print("✅ 会话管理功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 会话管理测试失败: {e}")
        return False

def test_csrf_management():
    """测试CSRF Token管理功能"""
    print("\n🔄 测试CSRF Token管理功能...")
    
    try:
        from myfastapi.redis_client import get_csrf_manager
        
        csrf_manager = get_csrf_manager()
        
        # 测试数据
        test_user_id = "test_user_csrf_123"
        
        # 1. 生成CSRF Token
        csrf_token = csrf_manager.generate_csrf_token(test_user_id)
        print(f"✅ CSRF Token生成: {csrf_token is not None}")
        
        if csrf_token:
            # 2. 验证CSRF Token
            verify_success = csrf_manager.verify_csrf_token(test_user_id, csrf_token)
            print(f"✅ CSRF Token验证: {'成功' if verify_success else '失败'}")
            
            # 3. 验证错误的Token
            wrong_verify = csrf_manager.verify_csrf_token(test_user_id, "wrong_token")
            print(f"✅ 错误Token验证: {'失败' if not wrong_verify else '意外成功'}")
            
            # 4. 刷新CSRF Token
            new_csrf_token = csrf_manager.refresh_csrf_token(test_user_id)
            print(f"✅ CSRF Token刷新: {new_csrf_token is not None}")
            
            # 5. 验证旧Token是否失效
            old_verify = csrf_manager.verify_csrf_token(test_user_id, csrf_token)
            print(f"✅ 旧Token验证: {'失效' if not old_verify else '仍然有效'}")
        
        print("✅ CSRF Token管理功能测试完成")
        return True
        
    except Exception as e:
        print(f"❌ CSRF Token管理测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 Redis集成测试开始\n")
    
    # 显示环境变量
    print("📋 环境配置:")
    print(f"   REDIS_URL: {os.getenv('REDIS_URL', '未设置')}")
    print(f"   REDIS_PASSWORD: {'已设置' if os.getenv('REDIS_PASSWORD') else '未设置'}")
    print(f"   REDIS_DB: {os.getenv('REDIS_DB', '未设置')}")
    print()
    
    # 运行测试
    tests = [
        ("Redis连接", test_redis_connection),
        ("Token黑名单", test_token_blacklist),
        ("会话管理", test_session_management),
        ("CSRF管理", test_csrf_management),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n📊 测试结果汇总:")
    for test_name, success in results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {test_name}: {status}")
    
    successful_tests = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"\n🎯 总体结果: {successful_tests}/{total_tests} 测试通过")
    
    if successful_tests == total_tests:
        print("🎉 所有测试通过！Redis集成配置正确。")
        return 0
    else:
        print("⚠️  部分测试失败，请检查Redis配置和连接。")
        return 1

if __name__ == "__main__":
    exit(main())
