# strategy.py

import logging
from app.DatabaseOperator.pg_operator import Session
import pandas as pd

# 初始化日志
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')