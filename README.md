crypto_trader/
├── config.py              # 配置文件：API密钥、数据库配置等
├── database.py            # 数据库连接与模型定义
├── fetcher.py             # 第一步：价格采集
├── calculator.py          # 第二步：差额计算
├── strategy.py            # 第三步：策略判断
├── trader.py              # 第四步：交易执行
└── main.py                # 主程序，调用调度各模块
