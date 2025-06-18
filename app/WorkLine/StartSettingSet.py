import redis
import logging
import logging.config
import os
import sys
from pathlib import Path

# 先设置路径，以便导入 PathUniti
current_file = Path(__file__)
app_dir = current_file.parent.parent  # WorkLine -> app
if str(app_dir) not in sys.path:
    sys.path.insert(0, str(app_dir))
# 现在可以导入 PathUniti 和其他模块
from PathUniti import APP_DIR, get_log_file
from DatabaseOperator.pg_operator import Session, engine
from DatabaseOperator.redis_operator import RedisClient

# 简化的日志配置
def setup_logging():
    """配置日志记录"""
    # 获取日志文件路径
    log_file = get_log_file('StartSettingSet.log')
    
    # 配置根日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )

# 设置日志
setup_logging()

# 获取日志记录器
logger = logging.getLogger()

def Get_worklist():
    # 引入 RedisClient
    redis_client = RedisClient().client

    # 写入和读取数据
    redis_client.set("token", "abc123", ex=60)
    print(redis_client.get("token"))

    # 检查连接是否正常
    print(RedisClient().is_connected())

    # 查看 Redis 状态信息
    print(RedisClient().get_info())

def main():
    """主函数"""
    logger.info("开始获取工作列表...")
    try:
        Get_worklist()
        logger.info("工作列表获取成功")
    except Exception as e:
        logger.error(f"获取工作列表失败: {e}")

if __name__ == "__main__":
    # 运行主函数
    main()