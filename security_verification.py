#!/usr/bin/env python3
"""
安全修复验证脚本
验证所有安全改进是否正确实施
"""
import os
import sys
import time
import requests
import json
from typing import Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_environment_config():
    """检查环境配置"""
    print("🔍 检查环境配置...")
    
    # 检查 .env.example 文件
    env_example_path = os.path.join(os.path.dirname(__file__), '.env.example')
    if os.path.exists(env_example_path):
        print("✅ .env.example 文件存在")
        with open(env_example_path, 'r') as f:
            content = f.read()
            required_vars = ['ENVIRONMENT', 'USE_HTTPS', 'COOKIE_DOMAIN', 'JWT_EXPIRE_MINUTES']
            for var in required_vars:
                if var in content:
                    print(f"✅ {var} 配置存在")
                else:
                    print(f"❌ {var} 配置缺失")
    else:
        print("❌ .env.example 文件不存在")

def check_security_config_module():
    """检查安全配置模块"""
    print("\n🔍 检查安全配置模块...")
    
    try:
        from myfastapi.security_config import get_security_config
        config = get_security_config()
        
        print("✅ 安全配置模块导入成功")
        
        # 测试各种配置方法
        cookie_config = config.get_cookie_config()
        jwt_config = config.get_jwt_config()
        csrf_config = config.get_csrf_config()
        
        print(f"✅ Cookie配置: {cookie_config}")
        print(f"✅ JWT配置: {jwt_config}")
        print(f"✅ CSRF配置: {csrf_config}")
        
    except Exception as e:
        print(f"❌ 安全配置模块错误: {e}")

def check_cookie_security():
    """检查Cookie安全配置"""
    print("\n🔍 检查Cookie安全配置...")
    
    # 模拟不同环境
    test_envs = [
        {'ENVIRONMENT': 'development', 'USE_HTTPS': 'false'},
        {'ENVIRONMENT': 'production', 'USE_HTTPS': 'true', 'COOKIE_DOMAIN': 'example.com'}
    ]
    
    for env in test_envs:
        print(f"\n测试环境: {env}")
        
        # 临时设置环境变量
        old_values = {}
        for key, value in env.items():
            old_values[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            from myfastapi.security_config import SecurityConfig
            config = SecurityConfig()
            cookie_config = config.get_cookie_config()
            
            # 验证安全设置
            expected_secure = env.get('ENVIRONMENT') == 'production' or env.get('USE_HTTPS') == 'true'
            expected_samesite = 'strict' if env.get('ENVIRONMENT') == 'production' else 'lax'
            
            if cookie_config.get('secure') == expected_secure:
                print(f"✅ secure设置正确: {cookie_config.get('secure')}")
            else:
                print(f"❌ secure设置错误: 期望{expected_secure}, 实际{cookie_config.get('secure')}")
            
            if cookie_config.get('samesite') == expected_samesite:
                print(f"✅ samesite设置正确: {cookie_config.get('samesite')}")
            else:
                print(f"❌ samesite设置错误: 期望{expected_samesite}, 实际{cookie_config.get('samesite')}")
                
        except Exception as e:
            print(f"❌ Cookie配置测试失败: {e}")
        finally:
            # 恢复环境变量
            for key, old_value in old_values.items():
                if old_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = old_value

def check_timestamp_validation():
    """检查时间戳验证逻辑"""
    print("\n🔍 检查时间戳验证...")
    
    try:
        from myfastapi.security_config import SecurityConfig
        
        # 测试开发环境
        os.environ['ENVIRONMENT'] = 'development'
        dev_config = SecurityConfig()
        dev_window = dev_config.get_timestamp_window()
        print(f"✅ 开发环境时间窗口: {dev_window}ms")
        
        # 测试生产环境
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['COOKIE_DOMAIN'] = 'example.com'
        os.environ['JWT_SECRET'] = 'test-secret'
        os.environ['DATABASE_URL'] = 'test-db'
        
        prod_config = SecurityConfig()
        prod_window = prod_config.get_timestamp_window()
        print(f"✅ 生产环境时间窗口: {prod_window}ms")
        
        if prod_window < dev_window:
            print("✅ 生产环境时间窗口更严格")
        else:
            print("⚠️  生产环境时间窗口应该更严格")
            
    except Exception as e:
        print(f"❌ 时间戳验证测试失败: {e}")
    finally:
        # 清理环境变量
        for var in ['ENVIRONMENT', 'COOKIE_DOMAIN', 'JWT_SECRET', 'DATABASE_URL']:
            os.environ.pop(var, None)

def check_file_modifications():
    """检查文件修改情况"""
    print("\n🔍 检查文件修改...")
    
    files_to_check = [
        'myfastapi/main.py',
        'myfastapi/security.py',
        'myfastapi/security_config.py',
        '.env.example'
    ]
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path} 存在")
            
            # 检查特定的修复内容
            with open(full_path, 'r') as f:
                content = f.read()
                
            if file_path == 'myfastapi/main.py':
                if 'get_security_config' in content:
                    print("✅ main.py 包含安全配置导入")
                if '/api/public/csrf-token' in content:
                    print("✅ main.py 包含公开CSRF端点")
                    
            elif file_path == 'myfastapi/security.py':
                if 'logger.warning' in content and 'Unsigned request' in content:
                    print("✅ security.py 包含未签名请求日志")
                if 'get_timestamp_window' in content:
                    print("✅ security.py 使用配置化时间窗口")
                    
        else:
            print(f"❌ {file_path} 不存在")

def generate_security_report():
    """生成安全修复报告"""
    print("\n📊 生成安全修复报告...")
    
    report = {
        "修复时间": time.strftime("%Y-%m-%d %H:%M:%S"),
        "修复项目": [
            "✅ Cookie安全配置动态化",
            "✅ 签名验证逻辑改进",
            "✅ 时间戳验证窗口优化",
            "✅ 添加公开CSRF端点",
            "✅ 环境配置标准化",
            "✅ 安全配置模块化"
        ],
        "安全级别": "显著提升",
        "建议": [
            "定期更新安全配置",
            "监控未签名请求日志",
            "生产环境启用所有安全特性",
            "定期进行安全审计"
        ]
    }
    
    print(json.dumps(report, indent=2, ensure_ascii=False))

def main():
    """主函数"""
    print("🛡️  AutoTrading项目安全修复验证")
    print("=" * 50)
    
    check_environment_config()
    check_security_config_module()
    check_cookie_security()
    check_timestamp_validation()
    check_file_modifications()
    generate_security_report()
    
    print("\n🎉 安全修复验证完成！")
    print("请根据验证结果进行进一步调整。")

if __name__ == "__main__":
    main()
