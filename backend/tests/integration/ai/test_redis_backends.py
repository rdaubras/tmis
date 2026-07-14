import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("TMIS_REDIS_URL"),
    reason="Redis-backed integration tests require a running Redis instance "
    "(see docker-compose.yml).",
)


@pytest.mark.asyncio
async def test_redis_cache_roundtrip() -> None:
    from redis.asyncio import from_url

    from tmis.ai.cache.redis_cache import RedisCache

    client = from_url(os.environ["TMIS_REDIS_URL"])
    cache = RedisCache(client, key_prefix="tmis:test:cache:")
    try:
        await cache.set("k", "v", ttl_seconds=30)
        assert await cache.get("k") == "v"
        assert await cache.exists("k") is True
        await cache.delete("k")
        assert await cache.get("k") is None
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_make_cache_selects_redis_when_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    from tmis.ai.cache import factory
    from tmis.ai.cache.redis_cache import RedisCache
    from tmis.core.config import Settings

    monkeypatch.setattr(
        factory, "get_settings", lambda: Settings(redis_url=os.environ["TMIS_REDIS_URL"])
    )
    factory._shared_redis_client.cache_clear()
    try:
        cache = factory.make_cache()
        assert isinstance(cache, RedisCache)

        await cache.set("factory-roundtrip", "value", ttl_seconds=30)
        assert await cache.get("factory-roundtrip") == "value"
        await cache.delete("factory-roundtrip")
    finally:
        factory._shared_redis_client.cache_clear()


@pytest.mark.asyncio
async def test_redis_memory_store_roundtrip() -> None:
    import uuid

    from redis.asyncio import from_url

    from tmis.ai.memory.redis_store import RedisMemoryStore

    client = from_url(os.environ["TMIS_REDIS_URL"])
    store = RedisMemoryStore(client, key_prefix="tmis:test:memory:")
    key = f"conversation:{uuid.uuid4()}"
    try:
        await store.append(key, "user: bonjour")
        await store.append(key, "assistant: bonjour !")
        assert await store.get(key) == ["user: bonjour", "assistant: bonjour !"]
        await store.clear(key)
        assert await store.get(key) == []
    finally:
        await client.aclose()
