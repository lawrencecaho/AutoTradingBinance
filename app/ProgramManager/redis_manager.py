#!/usr/bin/env python3
"""
Redis管理工具
集成Redis配置、监控、测试和维护功能
"""
import os
import sys
import time
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class Colors:
    """终端颜色常量"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class RedisManager:
    """Redis管理器"""
    
    def __init__(self):
        self.redis_client = None
        self.token_blacklist = None
        self.session_manager = None
        self.csrf_manager = None
        self._initialize_redis()
    
    def _initialize_redis(self):
        """初始化Redis组件"""
        try:
            from myfastapi.redis_client import (
                get_redis_client, 
                get_token_blacklist, 
                get_session_manager, 
                get_csrf_manager
            )
            self.redis_client = get_redis_client()
            self.token_blacklist = get_token_blacklist()
            self.session_manager = get_session_manager()
            self.csrf_manager = get_csrf_manager()
            return True
        except ImportError as e:
            self.print_colored(f"❌ Redis模块导入失败: {e}", Colors.FAIL)
            return False
        except Exception as e:
            self.print_colored(f"❌ Redis初始化失败: {e}", Colors.FAIL)
            return False
    
    def print_colored(self, message: str, color: str = ""):
        """打印带颜色的消息"""
        print(f"{color}{message}{Colors.ENDC}")
    
    def print_header(self, title: str):
        """打印标题"""
        self.print_colored(f"\n{'=' * 60}", Colors.HEADER)
        self.print_colored(f"{title:^60}", Colors.HEADER + Colors.BOLD)
        self.print_colored(f"{'=' * 60}", Colors.HEADER)
    
    def show_config(self):
        """显示Redis配置信息"""
        self.print_header("Redis 配置信息")
        
        config_items = [
            ("REDIS_URL", os.getenv("REDIS_URL", "未设置")),
            ("REDIS_PASSWORD", "已设置" if os.getenv("REDIS_PASSWORD") else "未设置"),
            ("REDIS_DB", os.getenv("REDIS_DB", "未设置")),
        ]
        
        for key, value in config_items:
            color = Colors.OKGREEN if value != "未设置" else Colors.WARNING
            self.print_colored(f"  {key:15}: {value}", color)
    
    def test_connection(self) -> bool:
        """测试Redis连接"""
        self.print_header("Redis 连接测试")
        
        if not self.redis_client:
            self.print_colored("❌ Redis客户端未初始化", Colors.FAIL)
            return False
        
        try:
            # 检查连接状态
            is_connected = self.redis_client.is_connected()
            
            if is_connected:
                self.print_colored("✅ Redis连接成功", Colors.OKGREEN)
                
                # 获取Redis信息
                info = self.redis_client.get_info()
                
                info_items = [
                    ("Redis版本", info.get('redis_version', 'unknown')),
                    ("内存使用", info.get('used_memory_human', 'unknown')),
                    ("连接客户端数", info.get('connected_clients', 0)),
                    ("运行时间", f"{info.get('uptime_in_seconds', 0)} 秒"),
                    ("键空间命中率", f"{info.get('keyspace_hit_rate', 'N/A')}"),
                ]
                
                for label, value in info_items:
                    self.print_colored(f"  {label:15}: {value}", Colors.OKBLUE)
                
                return True
            else:
                self.print_colored("❌ Redis连接失败", Colors.FAIL)
                return False
                
        except Exception as e:
            self.print_colored(f"❌ 连接测试异常: {e}", Colors.FAIL)
            return False
    
    def test_token_blacklist(self) -> bool:
        """测试Token黑名单功能"""
        self.print_header("Token 黑名单功能测试")
        
        if not self.token_blacklist:
            self.print_colored("❌ Token黑名单管理器未初始化", Colors.FAIL)
            return False
        
        try:
            # 测试数据
            test_jti = f"test_token_{int(time.time())}"
            test_expires = 30  # 30秒过期
            
            self.print_colored(f"🔄 测试Token: {test_jti}", Colors.OKBLUE)
            
            # 1. 检查初始状态
            is_revoked_initial = self.token_blacklist.is_token_revoked(test_jti)
            self.print_colored(f"  初始状态: {'已撤销' if is_revoked_initial else '未撤销'}", 
                              Colors.WARNING if is_revoked_initial else Colors.OKGREEN)
            
            # 2. 撤销Token
            revoke_success = self.token_blacklist.revoke_token(test_jti, test_expires)
            self.print_colored(f"  撤销操作: {'成功' if revoke_success else '失败'}", 
                              Colors.OKGREEN if revoke_success else Colors.FAIL)
            
            # 3. 检查撤销后状态
            is_revoked_after = self.token_blacklist.is_token_revoked(test_jti)
            self.print_colored(f"  撤销后状态: {'已撤销' if is_revoked_after else '未撤销'}", 
                              Colors.OKGREEN if is_revoked_after else Colors.FAIL)
            
            # 4. 获取撤销信息
            revoke_info = self.token_blacklist.get_revoked_token_info(test_jti)
            if revoke_info:
                self.print_colored(f"  撤销时间: {revoke_info.get('revoked_at', 'N/A')}", Colors.OKBLUE)
            
            # 5. 统计信息
            count = self.token_blacklist.cleanup_expired_tokens()
            self.print_colored(f"  黑名单总数: {count}", Colors.OKBLUE)
            
            return revoke_success and is_revoked_after
            
        except Exception as e:
            self.print_colored(f"❌ Token黑名单测试失败: {e}", Colors.FAIL)
            return False
    
    def test_session_management(self) -> bool:
        """测试会话管理功能"""
        self.print_header("会话管理功能测试")
        
        if not self.session_manager:
            self.print_colored("❌ 会话管理器未初始化", Colors.FAIL)
            return False
        
        try:
            # 测试数据
            test_user_id = f"test_user_{int(time.time())}"
            test_session_data = {
                "ip_address": "192.168.1.100",
                "user_agent": "Redis Manager Test",
                "login_time": time.time()
            }
            
            self.print_colored(f"🔄 测试用户: {test_user_id}", Colors.OKBLUE)
            
            # 1. 创建会话
            session_id = self.session_manager.create_session(test_user_id, test_session_data.copy())
            self.print_colored(f"  会话创建: {'成功' if session_id else '失败'}", 
                              Colors.OKGREEN if session_id else Colors.FAIL)
            
            if not session_id:
                return False
            
            # 2. 获取会话
            session_data = self.session_manager.get_session(session_id)
            self.print_colored(f"  会话获取: {'成功' if session_data else '失败'}", 
                              Colors.OKGREEN if session_data else Colors.FAIL)
            
            # 3. 更新会话
            test_session_data["last_action"] = "redis_manager_test"
            update_success = self.session_manager.update_session(session_id, test_session_data)
            self.print_colored(f"  会话更新: {'成功' if update_success else '失败'}", 
                              Colors.OKGREEN if update_success else Colors.FAIL)
            
            # 4. 获取用户会话列表
            user_sessions = self.session_manager.get_user_sessions(test_user_id)
            self.print_colored(f"  用户会话数: {len(user_sessions)}", Colors.OKBLUE)
            
            # 5. 删除会话
            delete_success = self.session_manager.delete_session(session_id)
            self.print_colored(f"  会话删除: {'成功' if delete_success else '失败'}", 
                              Colors.OKGREEN if delete_success else Colors.FAIL)
            
            return all([session_id, session_data, update_success, delete_success])
            
        except Exception as e:
            self.print_colored(f"❌ 会话管理测试失败: {e}", Colors.FAIL)
            return False
    
    def test_csrf_management(self) -> bool:
        """测试CSRF Token管理功能"""
        self.print_header("CSRF Token 管理功能测试")
        
        if not self.csrf_manager:
            self.print_colored("❌ CSRF管理器未初始化", Colors.FAIL)
            return False
        
        try:
            # 测试数据
            test_user_id = f"test_user_csrf_{int(time.time())}"
            
            self.print_colored(f"🔄 测试用户: {test_user_id}", Colors.OKBLUE)
            
            # 1. 生成CSRF Token
            csrf_token = self.csrf_manager.generate_csrf_token(test_user_id)
            self.print_colored(f"  Token生成: {'成功' if csrf_token else '失败'}", 
                              Colors.OKGREEN if csrf_token else Colors.FAIL)
            
            if not csrf_token:
                return False
            
            # 2. 验证正确Token
            verify_success = self.csrf_manager.verify_csrf_token(test_user_id, csrf_token)
            self.print_colored(f"  Token验证: {'成功' if verify_success else '失败'}", 
                              Colors.OKGREEN if verify_success else Colors.FAIL)
            
            # 3. 验证错误Token
            wrong_verify = self.csrf_manager.verify_csrf_token(test_user_id, "wrong_token")
            self.print_colored(f"  错误Token验证: {'正确拒绝' if not wrong_verify else '意外通过'}", 
                              Colors.OKGREEN if not wrong_verify else Colors.FAIL)
            
            # 4. 刷新Token
            new_csrf_token = self.csrf_manager.refresh_csrf_token(test_user_id)
            self.print_colored(f"  Token刷新: {'成功' if new_csrf_token else '失败'}", 
                              Colors.OKGREEN if new_csrf_token else Colors.FAIL)
            
            # 5. 验证旧Token失效
            old_verify = self.csrf_manager.verify_csrf_token(test_user_id, csrf_token)
            self.print_colored(f"  旧Token失效: {'是' if not old_verify else '否'}", 
                              Colors.OKGREEN if not old_verify else Colors.WARNING)
            
            return all([csrf_token, verify_success, not wrong_verify, new_csrf_token])
            
        except Exception as e:
            self.print_colored(f"❌ CSRF管理测试失败: {e}", Colors.FAIL)
            return False
    
    def monitor_redis(self, interval: int = 5, count: int = 10):
        """监控Redis状态"""
        self.print_header(f"Redis 实时监控 (间隔: {interval}s, 次数: {count})")
        
        if not self.redis_client:
            self.print_colored("❌ Redis客户端未初始化", Colors.FAIL)
            return
        
        try:
            for i in range(count):
                if not self.redis_client.is_connected():
                    self.print_colored(f"❌ 第{i+1}次检查: Redis连接断开", Colors.FAIL)
                    break
                
                info = self.redis_client.get_info()
                timestamp = time.strftime("%H:%M:%S")
                
                memory_used = info.get('used_memory_human', 'N/A')
                clients = info.get('connected_clients', 0)
                ops_per_sec = info.get('instantaneous_ops_per_sec', 0)
                
                self.print_colored(
                    f"[{timestamp}] 内存: {memory_used} | 客户端: {clients} | 操作/秒: {ops_per_sec}",
                    Colors.OKGREEN
                )
                
                if i < count - 1:  # 最后一次不需要等待
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            self.print_colored("\n⏹️  监控已停止", Colors.WARNING)
        except Exception as e:
            self.print_colored(f"❌ 监控异常: {e}", Colors.FAIL)
    
    def cleanup_expired_data(self):
        """清理过期数据"""
        self.print_header("清理过期数据")
        
        try:
            # 清理Token黑名单
            if self.token_blacklist:
                token_count = self.token_blacklist.cleanup_expired_tokens()
                self.print_colored(f"  Token黑名单: {token_count} 个活跃Token", Colors.OKBLUE)
            
            # 注意：Redis会自动清理过期键，这里主要是统计信息
            self.print_colored("✅ 清理完成 (Redis自动处理过期键)", Colors.OKGREEN)
            
        except Exception as e:
            self.print_colored(f"❌ 清理失败: {e}", Colors.FAIL)
    
    def show_statistics(self):
        """显示Redis统计信息"""
        self.print_header("Redis 统计信息")
        
        if not self.redis_client:
            self.print_colored("❌ Redis客户端未初始化", Colors.FAIL)
            return
        
        try:
            if not self.redis_client.is_connected():
                self.print_colored("❌ Redis未连接", Colors.FAIL)
                return
            
            info = self.redis_client.get_info()
            
            # 内存统计
            self.print_colored("\n📊 内存统计:", Colors.OKBLUE + Colors.BOLD)
            memory_stats = [
                ("已使用内存", info.get('used_memory_human', 'N/A')),
                ("内存峰值", info.get('used_memory_peak_human', 'N/A')),
                ("内存碎片率", f"{info.get('mem_fragmentation_ratio', 'N/A')}"),
            ]
            for label, value in memory_stats:
                self.print_colored(f"  {label:15}: {value}", Colors.OKGREEN)
            
            # 连接统计
            self.print_colored("\n🔗 连接统计:", Colors.OKBLUE + Colors.BOLD)
            connection_stats = [
                ("当前连接数", info.get('connected_clients', 'N/A')),
                ("总连接数", info.get('total_connections_received', 'N/A')),
                ("被拒绝连接数", info.get('rejected_connections', 'N/A')),
            ]
            for label, value in connection_stats:
                self.print_colored(f"  {label:15}: {value}", Colors.OKGREEN)
            
            # 性能统计
            self.print_colored("\n⚡ 性能统计:", Colors.OKBLUE + Colors.BOLD)
            performance_stats = [
                ("总命令数", info.get('total_commands_processed', 'N/A')),
                ("每秒操作数", info.get('instantaneous_ops_per_sec', 'N/A')),
                ("键空间命中数", info.get('keyspace_hits', 'N/A')),
                ("键空间未命中数", info.get('keyspace_misses', 'N/A')),
            ]
            for label, value in performance_stats:
                self.print_colored(f"  {label:15}: {value}", Colors.OKGREEN)
            
            # 计算命中率
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            if hits + misses > 0:
                hit_rate = (hits / (hits + misses)) * 100
                self.print_colored(f"  {'键空间命中率':15}: {hit_rate:.2f}%", Colors.OKGREEN)
            
        except Exception as e:
            self.print_colored(f"❌ 获取统计信息失败: {e}", Colors.FAIL)
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        self.print_colored("\n🚀 开始Redis集成测试", Colors.HEADER + Colors.BOLD)
        
        tests = [
            ("连接测试", self.test_connection),
            ("Token黑名单", self.test_token_blacklist),
            ("会话管理", self.test_session_management),
            ("CSRF管理", self.test_csrf_management),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                success = test_func()
                results.append((test_name, success))
            except Exception as e:
                self.print_colored(f"❌ {test_name}测试异常: {e}", Colors.FAIL)
                results.append((test_name, False))
        
        # 显示结果
        self.print_header("测试结果汇总")
        for test_name, success in results:
            status = "✅ 通过" if success else "❌ 失败"
            color = Colors.OKGREEN if success else Colors.FAIL
            self.print_colored(f"  {test_name:15}: {status}", color)
        
        successful_tests = sum(1 for _, success in results if success)
        total_tests = len(results)
        
        self.print_colored(f"\n🎯 总体结果: {successful_tests}/{total_tests} 测试通过", 
                          Colors.OKGREEN if successful_tests == total_tests else Colors.WARNING)
        
        return successful_tests == total_tests

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Redis管理工具")
    parser.add_argument("action", choices=[
        "config", "test", "monitor", "stats", "cleanup", "all"
    ], help="执行的操作")
    parser.add_argument("--interval", type=int, default=5, help="监控间隔(秒)")
    parser.add_argument("--count", type=int, default=10, help="监控次数")
    
    args = parser.parse_args()
    
    manager = RedisManager()
    
    if args.action == "config":
        manager.show_config()
    elif args.action == "test":
        success = manager.run_all_tests()
        sys.exit(0 if success else 1)
    elif args.action == "monitor":
        manager.monitor_redis(args.interval, args.count)
    elif args.action == "stats":
        manager.show_statistics()
    elif args.action == "cleanup":
        manager.cleanup_expired_data()
    elif args.action == "all":
        manager.show_config()
        manager.show_statistics()
        success = manager.run_all_tests()
        manager.cleanup_expired_data()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
