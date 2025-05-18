# BinanceActivity_RSA.py
# 使用 RSA 签名与 Binance Testnet 通信
# 功能包括：获取账户余额、提交限价买单、查看当前挂单

import time
import base64
import urllib.parse
import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from config import BINANCE_API_KEY, BINANCE_PRIVATE_KEY_PATH

# ==== 账户配置 ====
API_KEY = BINANCE_API_KEY
PRIVATE_KEY_PATH = BINANCE_PRIVATE_KEY_PATH

# ==== 通用签名函数 ====
def rsa_sign(query_string: str, private_key_path: str) -> str:
    with open(private_key_path, 'rb') as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )
    # 检查密钥类型
    from cryptography.hazmat.primitives.asymmetric import rsa
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise TypeError("私钥类型不是 RSA，请检查密钥文件！")
    signature = private_key.sign(
        query_string.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    return urllib.parse.quote_plus(signature_b64)

# ==== 构建并发送带签名请求 ====
def signed_request(method: str, endpoint: str, params: dict):
    base_url = "https://testnet.binance.vision"
    params['timestamp'] = str(int(time.time() * 1000))
    query_string = '&'.join([f"{key}={value}" for key, value in params.items()])
    signature = rsa_sign(query_string, PRIVATE_KEY_PATH)
    full_url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
    headers = {
        'X-MBX-APIKEY': API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.request(method, full_url, headers=headers)
    print(f"请求: {method} {endpoint}")
    print(f"响应状态: {response.status_code}")
    print(response.json())

# ==== 获取账户余额 ====
print("\n[账户余额]")
signed_request("GET", "/api/v3/account", {"recvWindow": "5000"})

#========================================
# 提示用户是否继续
print("\n请确认是否继续创建订单。")
print("如果需要返回，请输入 x；如果需要继续，请输入 y。")
# 这里使用了一个简单的循环来等待用户输入
# 注意：在实际应用中，可能需要更复杂的输入处理
# 例如，使用多线程或异步处理来避免阻塞
# 这里使用了一个简单的循环来等待用户输入
while True:
    user_input = input("请输入 y 继续，x 返回：").strip().lower()
    if user_input == 'y':
        print("继续执行...")
        break
    elif user_input == 'x':
        print("已返回。")
        break  # 顶层代码只能用 break，不能用 return
    else:
        print("无效输入，请重新输入。")
#========================================

# ==== 创建限价买单 ====
print("\n[创建限价买单]")
order_params = {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "LIMIT",
    "timeInForce": "GTC",
    "quantity": "0.001",
    "price": "20000",
    "recvWindow": "5000"
}
signed_request("POST", "/api/v3/order", order_params)

# ==== 查看当前挂单 ====
print("\n[当前挂单]")
signed_request("GET", "/api/v3/openOrders", {"symbol": "BTCUSDT", "recvWindow": "5000"})
