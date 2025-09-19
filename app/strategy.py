# strategy.py

import logging
from app.DatabaseOperator.pg_operator import Session
import pandas as pd
from config.logging_config import get_logger

# 获取日志记录器
logger = get_logger(__name__)