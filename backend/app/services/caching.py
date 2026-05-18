import os
import json
import redis
from typing import Optional, Any
from functools import wraps

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

try:
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    print(f"Warning: Redis connection failed - {e}")
    redis_client = None

def get_cache(key: str) -> Optional[Any]:
    if not redis_client:
        return None
    try:
        val = redis_client.get(key)
        if val:
            return json.loads(val)
    except Exception:
        pass
    return None

def set_cache(key: str, value: Any, ttl_seconds: int = 3600) -> bool:
    if not redis_client:
        return False
    try:
        redis_client.setex(key, ttl_seconds, json.dumps(value))
        return True
    except Exception:
        pass
    return False

def cache_response(ttl_seconds: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not redis_client:
                return await func(*args, **kwargs)
                
            # Create a simple cache key based on function name and stringified args
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached = get_cache(key)
            if cached is not None:
                return cached
                
            result = await func(*args, **kwargs)
            set_cache(key, result, ttl_seconds)
            return result
        return wrapper
    return decorator
