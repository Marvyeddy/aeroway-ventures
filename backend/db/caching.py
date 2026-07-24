import json
from typing import Any
from redis import RedisError
import redis.asyncio as aioredis
from backend.utils.config import Config as cfg


class RedisCache:
    def __init__(self):
        self.r = aioredis.from_url(url=cfg.REDIS_URL, decode_responses=True)

    def set(self, key: str, value: Any, expiry: int = 300):
        try:
            json_value = json.dumps(value)
            self.r.set(key, json_value, expiry)
            print(f"Cached key {key} for {expiry} seconds")
        except RedisError as e:
            print(f"Redis connection error: {e}")

    def get(self, key: str):
        try:
            json_value = self.r.get(key)
            if json_value:
                print(f"Cache hit for key {key}")
                return json.loads(json_value)
            print(f"Cache miss for key {key}")
            return None
        except RedisError as e:
            print(f"Redis connection error: {e}")
            return None


redis_cache = RedisCache()
