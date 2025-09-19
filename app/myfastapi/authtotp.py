# myfastapi/authtotp.py
'''
Create a new user and secret code
'''
import sys
import os
import pyotp
import qrcode
from DatabaseOperator import get_session # 使用模块提供的接口
from DatabaseOperator.pg_operator import dbinsert_common # 直接导入需要的函数
from sqlalchemy import Table, MetaData, create_engine
from config import DATABASE_URL
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import logging
from config.logging_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)

def generate_totp_secret():
    """生成新的 TOTP 密钥"""
    return pyotp.random_base32()

def generate_qr_code(totp_secret: str, username: str):
    """生成 TOTP 二维码"""
    totp = pyotp.TOTP(totp_secret)
    provisioning_uri = totp.provisioning_uri(username, issuer_name="AutoTradingBinance")
    
    # 创建二维码
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    
    # 创建 QRCodes 目录（如果不存在）
    qr_dir = Path(__file__).parent / 'QRCodes'
    qr_dir.mkdir(exist_ok=True)
    
    # 创建并保存二维码图片
    qr_image = qr.make_image(fill_color="black", back_color="white")
    qr_filename = f"totp_qr_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    qr_filepath = qr_dir / qr_filename
    
    # 使用with语句打开文件并保存
    with open(qr_filepath, 'wb') as f:
        qr_image.save(f)
    
    return str(qr_filepath)

def create_user(uid: str, username: str):
    """创建新用户并生成 TOTP 密钥"""
    Session = get_session()
    session = Session()
    try:
        # 生成 TOTP 密钥
        totp_secret = generate_totp_secret()
        
        # 使用 SQLAlchemy Core 插入数据
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()
        userbasic = Table('userbasic', metadata, autoload_with=engine)
        
        try:
            stmt = userbasic.insert().values(
                uid=uid,
                username=username,
                totpsecret=totp_secret,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            session.execute(stmt)
            session.commit()
            
            # 生成二维码
            qr_filename = generate_qr_code(totp_secret, username)
            
            logger.info(f"用户创建成功!")
            logger.info(f"UID: {uid}")
            logger.info(f"用户名: {username}")
            logger.info(f"TOTP 密钥: {totp_secret}")
            logger.info(f"二维码已保存为: {qr_filename}")
            logger.info("\n请使用 Google Authenticator 或其他 TOTP 应用扫描二维码")
            
            # 显示一个测试码，用于验证设置是否正确
            totp = pyotp.TOTP(totp_secret)
            current_otp = totp.now()
            logger.info(f"\n当前的 TOTP 码（用于测试）: {current_otp}")
            
            return True
            
        except Exception as e:
            logger.error(f"数据库插入错误: {str(e)}")
            session.rollback()
            return False
            
    except Exception as e:
        logger.error(f"创建用户时出错: {str(e)}")
        return False
    finally:
        session.close()

def verify_totp(uid: str, totp_code: str):
    """验证 TOTP 码"""
    Session = get_session()
    session = Session()
    try:
        # 获取用户的TOTP密钥
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()
        userbasic = Table('userbasic', metadata, autoload_with=engine)
        
        result = session.execute(
            userbasic.select().where(userbasic.c.uid == uid)
        ).fetchone()
        
        if not result or not result.totpsecret:
            return False
            
        # 验证TOTP码
        totp = pyotp.TOTP(result.totpsecret)
        return totp.verify(totp_code)
        
    except Exception as e:
        logger.error(f"TOTP验证出错: {str(e)}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TOTP 认证管理工具')
    parser.add_argument('action', choices=['create', 'verify'], help='执行的操作：create（创建新用户）或 verify（验证TOTP码）')
    parser.add_argument('--uid', required=True, help='用户ID')
    parser.add_argument('--username', help='用户名（仅用于创建用户）')
    parser.add_argument('--code', help='TOTP码（仅用于验证）')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        if not args.username:
            logger.error("创建用户时需要提供用户名")
            sys.exit(1)
        success = create_user(args.uid, args.username)
        sys.exit(0 if success else 1)
    
    elif args.action == 'verify':
        if not args.code:
            logger.error("验证时需要提供TOTP码")
            sys.exit(1)
        success = verify_totp(args.uid, args.code)
        if success:
            logger.info("TOTP验证成功")
            sys.exit(0)
        else:
            logger.error("TOTP验证失败")
            sys.exit(1)
