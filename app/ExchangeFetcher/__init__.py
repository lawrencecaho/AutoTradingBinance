# ExchangeFetcher Initialization

# 延迟导入，避免在包级别导入时出现依赖错误
def fetch_price(*args, **kwargs):
    from .fetcher import fetch_price as _fetch_price
    return _fetch_price(*args, **kwargs)

def get_kline(*args, **kwargs):
    from .fetcher import get_kline as _get_kline
    return _get_kline(*args, **kwargs)

__all__ = ['fetch_price', 'get_kline']