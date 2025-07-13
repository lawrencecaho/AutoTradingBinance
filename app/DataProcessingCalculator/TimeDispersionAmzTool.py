# 时间离散度分析工具，测试档
import numpy as np
import asyncio
from DatabaseOperator.pg_operator import Time_Discrete_Check


async def linear_score(delta_t, phi):
    """线性偏离度得分"""
    delta_t = np.asarray(delta_t)
    diffs = np.abs(delta_t - phi)
    return np.mean(1 - diffs / (phi + 1e-6))


async def continuity_index(delta_t, phi):
    """连续性指数"""
    delta_t = np.asarray(delta_t)
    std_dev = np.std(delta_t - phi)
    return 1 - (std_dev / phi)


async def exponential_score(delta_t, phi, p=4):
    """指数连续性得分"""
    delta_t = np.asarray(delta_t)
    penalty = np.mean(np.abs((delta_t - phi) / phi) ** p)
    return np.exp(-penalty)

async def analyze_time_dispersion(table_name, time_column, phi, days_ago):
    """分析时间离散度"""
    timestamps = Time_Discrete_Check(
        table_name=table_name, 
        time_column_name=time_column, 
        days_ago=days_ago
    )
    delta_t = np.diff([t.timestamp() / 60 for t in timestamps])
    
    # 三个公式同时执行
    linear_task = linear_score(delta_t, phi)
    continuity_task = continuity_index(delta_t, phi)
    exponential_task = exponential_score(delta_t, phi, p=2)
    
    # 等待所有计算完成
    linear_result, continuity_result, exponential_result = await asyncio.gather(
        linear_task, continuity_task, exponential_task
    )
    
    return {
        'linear': linear_result,
        'continuity': continuity_result, 
        'exponential': exponential_result
    }


# 使用示例
if __name__ == "__main__":
    async def main():
        # 示例调用
        result = await analyze_time_dispersion("KLine_ETHUSDT", "open_time", 60.0, 7)
        print(f"Linear: {result['linear']:.4f}")
        print(f"Continuity: {result['continuity']:.4f}")
        print(f"Exponential: {result['exponential']:.4f}")
    
    # 运行异步函数
    asyncio.run(main())
