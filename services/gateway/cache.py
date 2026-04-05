# services/gateway/cache.py
import redis.asyncio as redis
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

redis_client: Optional[redis.Redis] = None


async def connect_to_redis(redis_url: str):
    """Connect to Redis"""
    global redis_client
    redis_client = redis.from_url(redis_url, decode_responses=True)
    logger.info("Connected to Redis")


async def close_redis_connection():
    """Close Redis connection"""
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_cached_response(cache_key: str) -> Optional[dict]:
    """Get cached response from Redis"""
    cached = await redis_client.get(cache_key)
    if cached:
        logger.info(f"Cache hit: {cache_key}")
        return json.loads(cached)
    return None


async def set_cached_response(cache_key: str, data: dict, ttl: int = 300):
    """Set response in Redis cache"""
    await redis_client.setex(cache_key, ttl, json.dumps(data))
    logger.info(f"Cache set: {cache_key}")
