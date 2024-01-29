from functools import wraps
from django.core.cache import cache


def cached(seconds=60, key=None, version=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if key:
                cache_key = key
            else:
                cache_key = f'func:{func.__name__}'
            result = cache.get(cache_key)
            if not result:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, seconds, version)
            return result

        return wrapper

    return decorator
