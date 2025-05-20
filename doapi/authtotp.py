#/Users/cayeho/Project/Cryp/AutoTradingBinance/doapi/authtotp.py
import sys
import os
import pyotp
import qrcode
from database import Session, dbinsert_common
from sqlalchemy import Table, MetaData, create_engine
from config import DATABASE_URL
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
            
            print(f"用户创建成功!")
            print(f"UID: {uid}")
            print(f"用户名: {username}")
            print(f"TOTP 密钥: {totp_secret}")
            print(f"二维码已保存为: {qr_filename}")
            print("\n请使用 Google Authenticator 或其他 TOTP 应用扫描二维码")
            
            # 显示一个测试码，用于验证设置是否正确
            totp = pyotp.TOTP(totp_secret)
            current_otp = totp.now()
            print(f"\n当前的 TOTP 码（用于测试）: {current_otp}")
            
            return True
            
        except Exception as e:
            print(f"数据库插入错误: {str(e)}")
            session.rollback()
            return False
            
    except Exception as e:
        print(f"创建用户时出错: {str(e)}")
        return False
    finally:
        session.close()

def verify_totp(uid: str, totp_code: str):
    """验证 TOTP 码"""
    session = Session()
    try:
        # 查询用户的 TOTP 密钥
        engine = create_engine(DATABASE_URL)
        metadata = MetaData()
        userbasic = Table('userbasic', metadata, autoload_with=engine)
        
        result = session.query(userbasic).filter(userbasic.c.uid == uid).first()
        if not result:
            print("用户不存在")
            return False
            
        totp = pyotp.TOTP(result.totpsecret)
        return totp.verify(totp_code)
    
    finally:
        session.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TOTP 认证管理工具')
    parser.add_argument('--create', action='store_true', help='创建新用户')
    parser.add_argument('--verify', action='store_true', help='验证 TOTP 码')
    parser.add_argument('--uid', type=str, help='用户 UID')
    parser.add_argument('--username', type=str, help='用户名')
    parser.add_argument('--code', type=str, help='TOTP 验证码')
    
    args = parser.parse_args()
    
    if args.create:
        if not args.uid or not args.username:
            print("创建用户需要提供 --uid 和 --username")
        else:
            create_user(args.uid, args.username)
    
    elif args.verify:
        if not args.uid or not args.code:
            print("验证 TOTP 需要提供 --uid 和 --code")
        else:
            if verify_totp(args.uid, args.code):
                print("验证成功！")
            else:
                print("验证失败！")
    
    else:
        parser.print_help()
