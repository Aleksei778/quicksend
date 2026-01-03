import redis.asyncio as aioredis
from redis.asyncio import Redis

from common.config.base_config import base_settings
from common.log.logger import logger

_redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    global _redis_client

    if _redis_client is None:
        try:
            redis_url = base_settings.REDIS_URL

            _redis_client = aioredis.from_url(
                redis_url,
                decode_responses=True,
                encoding="utf-8",
                socket_connect_timeout=5,
                socket_keepalive=True,
            )

            await _redis_client.ping()

            logger.info(f"✅ Redis client created: {redis_url}")

        except Exception as e:
            logger.error(f"❌ Failed to create Redis client: {e}")

            raise

    return _redis_client


async def close_redis_client():
    global _redis_client

    if _redis_client:
        await _redis_client.close()

        _redis_client = None

        logger.info("✅ Redis client closed")
