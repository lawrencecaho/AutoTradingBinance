# WorkLine/master.py
"""
WorkLine module is used to manage the whole Project and let's Decision Maker to work.
"""
import logging
from config.logging_config import get_logger

from DatabaseOperator import get_pg_operator, get_redis_operator

logger = get_logger(__name__)

def main():

    """
    """