crypto_trader/
├── config.py              # 配置文件：API密钥、数据库配置等
├── database.py            # 数据库连接与模型定义
├── fetcher.py             # 第一步：价格采集
├── calculator.py          # 第二步：差额计算
├── strategy.py            # 第三步：策略判断
├── trader.py              # 第四步：交易执行
└── main.py                # 主程序，调用调度各模块

# 数据结构
## 数据表
Price

表名格式：price_data_{SYMBOL.lower()}

字段：

id：主键，整数类型。

symbol：交易对符号，字符串类型。

price：价格，浮点数类型。

timestamp：记录时间，日期时间类型。

PriceDiff

表名格式：price_diff_{SYMBOL.lower()}

字段：

id：主键，整数类型。

diff：价格差值，浮点数类型。

current_price：当前价格，浮点数类型。

buy_price：买入价格，浮点数类型。

timestamp：记录时间，日期时间类型。

BuyHistory

表名格式：buy_history_{SYMBOL.lower()}

字段：

id：主键，整数类型。

price：买入价格，浮点数类型。

quantity：买入数量，浮点数类型。

timestamp：记录时间，日期时间类型。

## 变量
current_price

类型：Price 表的实例

用途：存储查询得到的最新价格记录。

last_buy

类型：BuyHistory 表的实例

用途：存储最近一次买入记录。

diff

类型：浮点数

用途：表示当前价格与最近一次买入价格之间的差值。

latest_diff

类型：PriceDiff 表的实例

用途：存储最新一条价格差异记录。

decision

类型：元组或 None

用途：存储当前交易决策，格式为 (交易类型, 当前价格)，其中交易类型为 BUY 或 SELL。

说明
所有数据表均基于交易对符号动态生成表名，以支持多交易对场景。

变量用于连接数据库记录、执行交易逻辑判断与记录决策结果。

