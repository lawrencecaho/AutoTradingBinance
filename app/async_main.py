# async_main.py
# 异步版本的主程序

import asyncio
import aiohttp
import os
import sys
import time
import uvicorn
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import logging

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from config import FETCH_INTERVAL_SECONDS, StableUrl, SYMBOL
from app.DatabaseOperator.pg_operator import init_db, Session
# import asyncpg  # 需要安装: pip install asyncpg
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession  # 需要安装: pip install sqlalchemy[asyncio]
# from sqlalchemy.orm import sessionmaker

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AsyncBinanceClient:
    """异步Binance API客户端"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or StableUrl
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        timeout = aiohttp.ClientTimeout(total=10)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
            
    async def fetch_price(self, symbol: str) -> Optional[float]:
        """异步获取价格"""
        try:
            url = f'{self.base_url}ticker/price?symbol={symbol}'
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                price = float(data['price'])
                logger.info(f"获取 {symbol} 价格: {price}")
                return price
        except Exception as e:
            logger.error(f"获取 {symbol} 价格失败: {e}")
            return None
            
    async def fetch_kline(self, symbol: str, interval: str = "1m", limit: int = 100) -> Optional[List]:
        """异步获取K线数据"""
        try:
            url = f'{self.base_url}klines?symbol={symbol}&interval={interval}&limit={limit}'
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                logger.info(f"获取 {symbol} K线数据: {len(data)} 条")
                return data
        except Exception as e:
            logger.error(f"获取 {symbol} K线数据失败: {e}")
            return None
            
    async def fetch_multiple_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """并行获取多个交易对的价格"""
        tasks = [self.fetch_price(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        price_dict = {}
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception):
                logger.error(f"获取 {symbol} 价格时出现异常: {result}")
                price_dict[symbol] = None
            else:
                price_dict[symbol] = result
                
        return price_dict

class AsyncTradingEngine:
    """异步交易引擎"""
    
    def __init__(self):
        self.binance_client: Optional[AsyncBinanceClient] = None
        self.symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]  # 可以扩展更多交易对
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.binance_client = AsyncBinanceClient()
        await self.binance_client.__aenter__()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.binance_client:
            await self.binance_client.__aexit__(exc_type, exc_val, exc_tb)
            
    async def calculate_diff_async(self, current_price: float, previous_price: float) -> Dict[str, Any]:
        """异步计算价格差异"""
        # 模拟异步计算过程
        await asyncio.sleep(0.01)  # 模拟计算耗时
        
        if previous_price == 0:
            return {"diff": 0, "percentage": 0}
            
        diff = current_price - previous_price
        percentage = (diff / previous_price) * 100
        
        return {
            "diff": diff,
            "percentage": percentage,
            "current_price": current_price,
            "previous_price": previous_price
        }
        
    async def should_trade_async(self, price_data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """异步交易决策"""
        # 模拟异步决策过程
        await asyncio.sleep(0.05)  # 模拟决策耗时
        
        symbol = price_data.get("symbol", "UNKNOWN")
        current_price = price_data.get("price")
        percentage_change = analysis.get("percentage", 0)
        
        if current_price is None:
            return {"symbol": symbol, "action": "HOLD", "reason": "价格数据无效"}
        
        # 简单的交易策略
        if percentage_change > 2:
            return {"symbol": symbol, "action": "SELL", "reason": f"价格上涨 {percentage_change:.2f}%"}
        elif percentage_change < -2:
            return {"symbol": symbol, "action": "BUY", "reason": f"价格下跌 {percentage_change:.2f}%"}
        else:
            return {"symbol": symbol, "action": "HOLD", "reason": f"价格变化 {percentage_change:.2f}%，保持观望"}
            
    async def execute_trade_async(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行交易"""
        # 模拟异步交易执行
        await asyncio.sleep(0.1)  # 模拟交易耗时
        
        symbol = decision["symbol"]
        action = decision["action"]
        
        if action in ["BUY", "SELL"]:
            # 这里应该是实际的交易API调用
            logger.info(f"模拟执行交易: {action} {symbol}")
            return {
                "symbol": symbol,
                "action": action,
                "executed": True,
                "timestamp": datetime.now(timezone.utc),
                "status": "SUCCESS"
            }
        else:
            return {
                "symbol": symbol,
                "action": action,
                "executed": False,
                "timestamp": datetime.now(timezone.utc),
                "status": "HOLD"
            }
            
    async def process_symbol(self, symbol: str, price_history: Dict[str, float] = None) -> Dict[str, Any]:
        """处理单个交易对的完整流程"""
        if price_history is None:
            price_history = {}
            
        logger.info(f"开始处理 {symbol}")
        
        # 1. 获取当前价格
        current_price = await self.binance_client.fetch_price(symbol)
        if current_price is None:
            return {"symbol": symbol, "status": "ERROR", "message": "无法获取价格"}
        
        price_data = {"symbol": symbol, "price": current_price}
        
        # 2. 计算价格变化
        previous_price = price_history.get(symbol, current_price)
        analysis = await self.calculate_diff_async(current_price, previous_price)
        
        # 3. 做出交易决策
        decision = await self.should_trade_async(price_data, analysis)
        
        # 4. 执行交易
        trade_result = await self.execute_trade_async(decision)
        
        # 更新价格历史
        price_history[symbol] = current_price
        
        return {
            "symbol": symbol,
            "status": "SUCCESS",
            "price_data": price_data,
            "analysis": analysis,
            "decision": decision,
            "trade_result": trade_result
        }
        
    async def run_trading_cycle(self, price_history: Dict[str, float] = None) -> Dict[str, Any]:
        """运行一个完整的交易周期"""
        if price_history is None:
            price_history = {}
            
        logger.info("开始新的交易周期")
        start_time = time.time()
        
        # 并行处理所有交易对
        tasks = [self.process_symbol(symbol, price_history) for symbol in self.symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        cycle_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"处理交易对时出现异常: {result}")
            else:
                cycle_results.append(result)
        
        end_time = time.time()
        cycle_time = end_time - start_time
        
        logger.info(f"交易周期完成，耗时: {cycle_time:.2f}秒，处理了 {len(cycle_results)} 个交易对")
        
        return {
            "cycle_time": cycle_time,
            "results": cycle_results,
            "timestamp": datetime.now(timezone.utc)
        }
        
    async def run_continuous_trading(self, interval: int = None):
        """持续运行交易系统"""
        if interval is None:
            interval = FETCH_INTERVAL_SECONDS
            
        logger.info(f"开始持续交易，间隔: {interval}秒")
        
        price_history = {}
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                logger.info(f"开始第 {cycle_count} 个交易周期")
                
                # 运行交易周期
                cycle_result = await self.run_trading_cycle(price_history)
                
                # 打印周期摘要
                for result in cycle_result["results"]:
                    if result["status"] == "SUCCESS":
                        symbol = result["symbol"]
                        action = result["decision"]["action"]
                        price = result["price_data"]["price"]
                        change = result["analysis"]["percentage"]
                        logger.info(f"{symbol}: {action} @ {price} (变化: {change:.2f}%)")
                
                # 等待下一个周期
                logger.info(f"周期 {cycle_count} 完成，等待 {interval} 秒...")
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("收到停止信号，正在关闭交易系统...")
        except Exception as e:
            logger.error(f"交易系统运行时出现错误: {e}")
            raise

# 性能对比函数
async def performance_comparison():
    """比较同步和异步的性能"""
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "BNBUSDT", "XRPUSDT"]
    
    async with AsyncBinanceClient() as client:
        # 异步并行获取
        start_time = time.time()
        async_results = await client.fetch_multiple_prices(symbols)
        async_time = time.time() - start_time
        
        logger.info(f"异步并行获取 {len(symbols)} 个价格，耗时: {async_time:.2f}秒")
        
        # 异步顺序获取（模拟同步行为）
        start_time = time.time()
        sequential_results = {}
        for symbol in symbols:
            price = await client.fetch_price(symbol)
            sequential_results[symbol] = price
        sequential_time = time.time() - start_time
        
        logger.info(f"异步顺序获取 {len(symbols)} 个价格，耗时: {sequential_time:.2f}秒")
        logger.info(f"性能提升: {sequential_time / async_time:.2f}x")
        
        return async_results

async def main():
    """异步主函数"""
    logger.info("=== 异步交易系统启动 ===")
    
    # 性能对比演示
    logger.info("1. 性能对比演示")
    await performance_comparison()
    
    print("\n" + "="*50 + "\n")
    
    # 运行交易引擎
    logger.info("2. 启动交易引擎")
    async with AsyncTradingEngine() as trading_engine:
        # 运行几个交易周期作为演示
        for i in range(3):
            result = await trading_engine.run_trading_cycle()
            logger.info(f"演示周期 {i+1} 完成")
            if i < 2:  # 不在最后一次循环时等待
                await asyncio.sleep(2)
        
        # 可以取消注释下面的行来运行持续交易
        # await trading_engine.run_continuous_trading(10)

# FastAPI集成示例
async def create_fastapi_app():
    """创建集成异步功能的FastAPI应用"""
    from fastapi import FastAPI
    
    app = FastAPI(title="异步加密货币交易API")
    trading_engine = None
    
    @app.on_event("startup")
    async def startup_event():
        nonlocal trading_engine
        trading_engine = AsyncTradingEngine()
        await trading_engine.__aenter__()
        
    @app.on_event("shutdown")
    async def shutdown_event():
        if trading_engine:
            await trading_engine.__aexit__(None, None, None)
    
    @app.get("/prices/{symbols}")
    async def get_prices(symbols: str):
        """获取多个交易对的价格"""
        symbol_list = symbols.split(",")
        if trading_engine and trading_engine.binance_client:
            prices = await trading_engine.binance_client.fetch_multiple_prices(symbol_list)
            return {"prices": prices, "timestamp": datetime.now(timezone.utc)}
        return {"error": "交易引擎未初始化"}
    
    @app.post("/trading/cycle")
    async def run_trading_cycle():
        """手动运行一个交易周期"""
        if trading_engine:
            result = await trading_engine.run_trading_cycle()
            return result
        return {"error": "交易引擎未初始化"}
    
    return app

if __name__ == "__main__":
    # 选择运行模式
    import argparse
    
    parser = argparse.ArgumentParser(description='异步交易系统')
    parser.add_argument('--mode', choices=['demo', 'trading', 'api'], 
                       default='demo', help='运行模式')
    parser.add_argument('--port', type=int, default=8000, help='API服务端口')
    
    args = parser.parse_args()
    
    if args.mode == 'demo':
        # 运行演示
        asyncio.run(main())
    elif args.mode == 'trading':
        # 运行持续交易
        async def run_trading():
            async with AsyncTradingEngine() as trading_engine:
                await trading_engine.run_continuous_trading()
        asyncio.run(run_trading())
    elif args.mode == 'api':
        # 运行API服务
        app = asyncio.run(create_fastapi_app())
        uvicorn.run(app, host="0.0.0.0", port=args.port)
