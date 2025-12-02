import hashlib
import json
from typing import Any

import redis

from src.core.config import config

# Redis client
redis_client = redis.Redis(
    host=config.REDIS_HOST, port=config.REDIS_PORT, db=0, decode_responses=True
)


def get_cache_key(prefix: str, *args) -> str:
    """Generate a cache key from prefix and arguments."""
    key_data = f"{prefix}:{''.join(str(arg) for arg in args)}"
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cached(key: str) -> Any | None:
    """Get value from cache."""
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
    except Exception as e:
        print(f"Cache get error: {e}")
    return None


def set_cached(key: str, value: Any, ttl: int = 3600):
    """Set value in cache with TTL (default 1 hour)."""
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        print(f"Cache set error: {e}")


def delete_cached(pattern: str):
    """Delete keys matching pattern."""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        print(f"Cache delete error: {e}")


def clear_user_cache(user_id: int):
    """Clear all cache for a specific user."""
    delete_cached(f"*:user:{user_id}:*")
