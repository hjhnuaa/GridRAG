"""Tests for Redis cache fallback behavior."""

from __future__ import annotations

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from app.core.cache import RedisCache


class FailingRedis:
    """Redis stand-in that behaves like an unavailable local Redis service."""

    async def get(self, _: str) -> str | None:
        raise RedisConnectionError("redis unavailable")

    async def set(self, _: str, __: str, ex: int | None = None) -> None:
        raise RedisConnectionError("redis unavailable")

    async def delete(self, _: str) -> None:
        raise RedisConnectionError("redis unavailable")

    async def ping(self) -> bool:
        raise RedisConnectionError("redis unavailable")


@pytest.mark.asyncio
async def test_cache_read_degrades_to_miss_when_redis_unavailable() -> None:
    """Redis outages should behave like cache misses instead of breaking requests."""

    cache = RedisCache(FailingRedis())  # type: ignore[arg-type]

    assert await cache.get_json("stats:dashboard") is None


@pytest.mark.asyncio
async def test_cache_writes_and_deletes_are_best_effort_when_redis_unavailable() -> None:
    """Cache mutation failures should not block the primary database workflow."""

    cache = RedisCache(FailingRedis())  # type: ignore[arg-type]

    await cache.set_json("stats:dashboard", {"total": 1}, ttl=300)
    await cache.delete("stats:dashboard")


@pytest.mark.asyncio
async def test_cache_ping_returns_false_when_redis_unavailable() -> None:
    """Startup health probes should report Redis as unavailable without raising."""

    cache = RedisCache(FailingRedis())  # type: ignore[arg-type]

    assert await cache.ping() is False
