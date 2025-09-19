from ExchangeFetcher.fetcher import start_kline_websocket_sync
from DatabaseOperator import get_db_session

def realtime_monitor():
    """实时监控K线数据并立即写入数据库"""
    
    def kline_callback(kline_data):
        """K线数据回调函数"""
        status = "✅完结" if kline_data.get('is_closed', False) else "🔄实时"
        print(f"{status} {kline_data['symbol']} 价格:{kline_data['close']} 量:{kline_data['volume']}")
    
    print("🚀 **实时K线监控 - 自动提交模式**")
    print("=" * 50)
    print("💡 每条K线数据都会立即提交到数据库")
    print("🔍 你可以在运行过程中查询数据库看到实时数据")
    print("")
    
    with get_db_session() as session:
        # 获取ETHUSDT 1分钟K线，启用自动提交
        start_kline_websocket_sync(
            symbol="ETHUSDT",
            interval="1m",
            dbr=True,
            session=session,
            max_klines=10,
            auto_commit=True,  # 🔑 关键：启用自动提交
            callback=kline_callback
        )
    
    print("\n✅ 实时监控完成！")
    print("💾 所有数据都已实时写入数据库")

if __name__ == "__main__":
    realtime_monitor()