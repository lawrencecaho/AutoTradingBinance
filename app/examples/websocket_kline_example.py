#!/usr/bin/env python3
# app/examples/websocket_kline_example.py

"""
WebSocket K线数据获取示例

此文件展示如何使用 fetcher.py 中的 WebSocket K线功能
"""

import asyncio
import sys
import os

# 添加app目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ExchangeFetcher.fetcher import get_kline_websocket, start_kline_websocket_sync
from DatabaseOperator.pg_operator import Session


def print_kline_data(kline):
    """打印K线数据的回调函数"""
    print(f"📊 {kline['symbol']} {kline.get('interval', 'N/A')} K线数据:")
    print(f"  ⏰ 开盘时间: {kline['open_time']}")
    print(f"  💰 开盘价: {kline['open']}")
    print(f"  📈 最高价: {kline['high']}")
    print(f"  📉 最低价: {kline['low']}")
    print(f"  💰 收盘价: {kline['close']}")
    print(f"  📊 成交量: {kline['volume']}")
    print(f"  ✅ K线完结: {'是' if kline.get('is_closed') else '否'}")
    print("  " + "="*50)


async def example_basic_websocket():
    """基础WebSocket K线数据获取示例"""
    print("🚀 开始获取 BTCUSDT 1分钟 K线数据...")
    print("📝 将接收5个K线数据后停止\n")
    
    try:
        klines = await get_kline_websocket(
            symbol="BTCUSDT",
            interval="1m",
            callback=print_kline_data,
            max_klines=5,
            auto_reconnect=True
        )
        
        print(f"✅ 总共接收了 {len(klines)} 个K线数据")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


def example_sync_websocket():
    """同步方式使用WebSocket K线数据"""
    print("🚀 使用同步方式获取 ETHUSDT 1分钟 K线数据...")
    print("📝 将接收3个K线数据后停止\n")
    
    try:
        klines = start_kline_websocket_sync(
            symbol="ETHUSDT", 
            interval="1m",
            callback=print_kline_data,
            max_klines=3
        )
        
        print(f"✅ 同步方式总共接收了 {len(klines)} 个K线数据")
        
    except Exception as e:
        print(f"❌ 错误: {e}")


async def example_with_database():
    """带数据库存储的WebSocket K线示例"""
    print("🚀 获取K线数据并存储到数据库...")
    print("⚠️  注意：将获取ADAUSDT K线数据避免重复键冲突\n")
    
    session = Session()
    try:
        print("📋 创建数据库会话...")
        
        klines = await get_kline_websocket(
            symbol="ADAUSDT",  # 使用不同的交易对避免冲突
            interval="1m",
            dbr=True,  # 启用数据库写入
            session=session,
            callback=print_kline_data,
            max_klines=3  # 只获取3个避免时间过长
        )
        
        # 提交数据库事务
        session.commit()
        print(f"✅ 成功接收并存储了 {len(klines)} 个K线数据到数据库")
        
    except Exception as e:
        print(f"❌ 数据库示例错误: {e}")
    finally:
        if session:
            session.close()


async def example_multiple_symbols():
    """同时监控多个交易对的示例"""
    print("🚀 同时监控多个交易对的K线数据...\n")
    
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    tasks = []
    
    for symbol in symbols:
        task = asyncio.create_task(
            get_kline_websocket(
                symbol=symbol,
                interval="1m",
                callback=lambda kline, s=symbol: print(f"[{s}] {kline['close']}"),
                max_klines=2
            )
        )
        tasks.append(task)
    
    try:
        results = await asyncio.gather(*tasks)
        print(f"✅ 完成多交易对监控，共处理了 {len(results)} 个交易对")
    except Exception as e:
        print(f"❌ 多交易对监控错误: {e}")


if __name__ == "__main__":
    print("🎯 WebSocket K线数据获取示例")
    print("="*60)
    
    # 选择要运行的示例
    while True:
        print("\n请选择要运行的示例:")
        print("1. 基础WebSocket K线获取")
        print("2. 同步方式K线获取") 
        print("3. 带数据库存储(演示)")
        print("4. 多交易对同时监控")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-4): ").strip()
        
        if choice == "1":
            asyncio.run(example_basic_websocket())
        elif choice == "2":
            example_sync_websocket()
        elif choice == "3":
            asyncio.run(example_with_database())
        elif choice == "4":
            asyncio.run(example_multiple_symbols())
        elif choice == "0":
            print("👋 再见!")
            break
        else:
            print("❌ 无效选择，请重试")
