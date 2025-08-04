# WorkLine/master.py
"""
WorkLine module is used to manage the whole Project and let's Decision Maker to work.
"""
import logging

from DatabaseOperator import get_pg_operator, get_redis_operator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():

    """
    """