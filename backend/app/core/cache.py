"""Redis cache helpers."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, cast

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Minimal JSON-first cache wrapper around redis-py."""

    def __init__(self, client: Redis) -> None:
        """Initialize the cache wrapper."""

        self.client = client

    async def get_json(self, key: str) -> dict[str, Any] | list[Any] | None:
        """Read a JSON payload from Redis."""

        try:
            value = await self.client.get(key)
        except RedisError as exc:
            logger.warning("cache_read_failed", key=key, error=str(exc))
            return None
        if value is None:
            return None
        return cast(dict[str, Any] | list[Any], json.loads(value))

    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Write a JSON payload to Redis."""

        try:
            await self.client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
        except RedisError as exc:
            logger.warning("cache_write_failed", key=key, error=str(exc))

    async def delete(self, key: str) -> None:
        """Delete a cache key."""

        try:
            await self.client.delete(key)
        except RedisError as exc:
            logger.warning("cache_delete_failed", key=key, error=str(exc))

    async def ping(self) -> bool:
        """Check if Redis is reachable."""

        try:
            return bool(await self.client.ping())
        except RedisError:
            return False


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    """Return a cached Redis client."""

    settings = get_settings()
    return cast(
        Redis,
        Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True),
    )


@lru_cache(maxsize=1)
def get_cache() -> RedisCache:
    """Return the Redis cache wrapper."""

    return RedisCache(get_redis_client())
