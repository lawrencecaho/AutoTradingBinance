# BinanceActivity.py 文件：实现与 Binance API 的交互
# 主要功能：
# 1. 配置账户信息和交易参数
# 2. 初始化 Binance 客户端
# 3. 检查账户资产
# 4. 创建限价买入订单
# 5. 查看当前挂单

from binance.client import Client
from binance.enums import *
import time

# ==== 1. 账户配置（从 Binance Testnet 获取） ====
API_KEY= ''
PRIVATE_KEY_PATH= ''

# ==== 2. 交易参数设置，实际因从数据库中拉取 ====
SYMBOL = 'BTCUSDT'             # 交易对
QUANTITY = 0.001               # 购买数量（单位是 BTC）
PRICE = 20000                  # 限价价格（单位是 USDT）
ORDER_TYPE = ORDER_TYPE_LIMIT # 使用限价单
TIME_IN_FORCE = TIME_IN_FORCE_GTC  # GTC = Good Till Cancel，挂单直到成交或取消

# ==== 3. 初始化客户端，启用测试网络 ====
client = Client(API_KEY, API_SECRET, testnet=True)

# ==== 4. 检查账户资产（可选） ====
account = client.get_account()
print("账户余额信息：")
for balance in account['balances']:
    if float(balance['free']) > 0:
        print(f"{balance['asset']}: {balance['free']}")

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

# ==== 5. 创建限价买入订单 ====
try:
    order = client.create_order(
        symbol=SYMBOL,
        side=SIDE_BUY,
        type=ORDER_TYPE,
        timeInForce=TIME_IN_FORCE,
        quantity=QUANTITY,
        price=str(PRICE)  # 注意必须是字符串格式
    )
    print("\n✅ 订单已创建：")
    print(order)

except Exception as e:
    print("\n❌ 创建订单时出错：")
    print(e)

# ==== 6. 可选：查看当前挂单 ====
print("\n📋 当前挂单列表：")
open_orders = client.get_open_orders(symbol=SYMBOL)
for o in open_orders:
    print(o)
