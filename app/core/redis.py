import redis.asyncio as redis
from typing import Optional
from app.core.config import settings
from loguru import logger

class RedisClient:
    _instance: Optional[redis.Redis] = None

    @classmethod
    def get_instance(cls) -> redis.Redis:
        if cls._instance is None:
            if not settings.REDIS_URL:
                logger.warning("REDIS_URL not set. Caching will be disabled.")
                return None
            
            try:
                cls._instance = redis.from_url(
                    settings.REDIS_URL, 
                    encoding="utf-8", 
                    decode_responses=True
                )
                logger.info("Redis client initialized")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                return None
        return cls._instance

    @classmethod
    async def close(cls):
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            logger.info("Redis connection closed")

    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        r = cls.get_instance()
        if not r: return None
        try:
            return await r.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    @classmethod
    async def setex(cls, key: str, time: int, value: str):
        r = cls.get_instance()
        if not r: return
        try:
            await r.setex(key, time, value)
        except Exception as e:
            logger.error(f"Redis setex error: {e}")

# Global helper
async def get_redis() -> Optional[redis.Redis]:
    return RedisClient.get_instance()
