"""密钥生成工具"""
import os
import base64
import secrets
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

def generate_jwt_secret() -> str:
    """生成 JWT 密钥"""
    return secrets.token_urlsafe(32)

def generate_encryption_key() -> str:
    """生成 Fernet 加密密钥"""
    key = Fernet.generate_key()
    return key.decode()

def generate_api_secret() -> str:
    """生成 API 密钥"""
    return secrets.token_hex(32)

def generate_all_keys() -> dict:
    """生成所有需要的密钥"""
    return {
        'JWT_SECRET': generate_jwt_secret(),
        'ENCRYPTION_KEY': generate_encryption_key(),
        'API_SECRET_KEY': generate_api_secret()
    }

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    print("开始生成密钥...")
    
    # 生成所有密钥
    keys = generate_all_keys()
    print("\n生成的新密钥：")
    for key, value in keys.items():
        print(f"{key}: {value}")
    
    # 读取现有的 .env 文件
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    print(f"\n正在更新 .env 文件：{env_path}")
    
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
        print("成功读取现有的 .env 文件")
    except FileNotFoundError:
        print("未找到 .env 文件，将创建新文件")
        lines = []

    # 更新密钥
    new_lines = []
    updated_keys = set()
    
    # 保留注释和其他配置
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            new_lines.append(line)
            continue
            
        key = line.split('=')[0].strip()
        if key in keys:
            print(f"更新密钥：{key}")
            new_lines.append(f'{key}={keys[key]}')
            if key == 'ENCRYPTION_KEY':
                new_lines.append(f'NEXT_PUBLIC_ENCRYPT_KEY={keys[key]}')
            updated_keys.add(key)
        else:
            new_lines.append(line)
    
    # 添加缺失的密钥
    for key, value in keys.items():
        if key not in updated_keys:
            print(f"添加新密钥：{key}")
            new_lines.append(f'{key}={value}')
            if key == 'ENCRYPTION_KEY':
                new_lines.append(f'NEXT_PUBLIC_ENCRYPT_KEY={value}')
    
    # 写回文件
    print("\n正在保存更新后的 .env 文件...")
    try:
        with open(env_path, 'w') as f:
            f.write('\n'.join(new_lines) + '\n')
        print("密钥更新完成！")
    except IOError as e:
        print(f"保存文件时发生错误: {e}")
        logger.error(f"保存 .env 文件失败: {str(e)}")
    except Exception as e:
        print(f"发生未预期的错误: {e}")
        logger.error(f"更新密钥时发生未知错误: {str(e)}")
    finally:
        print("密钥生成程序执行完毕")