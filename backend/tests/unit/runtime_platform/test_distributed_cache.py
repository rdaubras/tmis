import asyncio

from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.runtime_platform.distributed_cache.engine import DistributedCacheEngine


def test_get_set_roundtrip_short_and_long_values() -> None:
    async def scenario() -> None:
        cache = DistributedCacheEngine(InMemoryCache())
        await cache.set("short", "hello")
        assert await cache.get("short") == "hello"

        long_value = "x" * 1000
        await cache.set("long", long_value, ttl_seconds=60)
        assert await cache.get("long") == long_value
        assert cache.stats.bytes_saved_by_compression > 0

    asyncio.run(scenario())


def test_invalidate_deletes_key_and_notifies_listeners() -> None:
    async def scenario() -> None:
        cache = DistributedCacheEngine(InMemoryCache())
        await cache.set("k", "v")
        seen: list[str] = []
        cache.register_invalidation_listener(seen.append)

        await cache.invalidate("k")

        assert seen == ["k"]
        assert await cache.get("k") is None
        assert cache.stats.invalidations == 1

    asyncio.run(scenario())


def test_warm_only_populates_missing_keys() -> None:
    async def scenario() -> None:
        cache = DistributedCacheEngine(InMemoryCache())
        await cache.set("existing", "already-there")
        calls = {"loader_calls": 0}

        async def loader_existing() -> str:
            calls["loader_calls"] += 1
            return "should-not-be-used"

        async def loader_new() -> str:
            return "fresh-value"

        warmed = await cache.warm(
            {"existing": loader_existing, "new": loader_new}, ttl_seconds=30
        )

        assert warmed == 1
        assert calls["loader_calls"] == 0
        assert await cache.get("existing") == "already-there"
        assert await cache.get("new") == "fresh-value"

    asyncio.run(scenario())


def test_hits_and_misses_are_tracked() -> None:
    async def scenario() -> None:
        cache = DistributedCacheEngine(InMemoryCache())
        await cache.get("missing")
        await cache.set("k", "v")
        await cache.get("k")

        assert cache.stats.misses == 1
        assert cache.stats.hits == 1
        assert cache.stats.sets == 1

    asyncio.run(scenario())


def test_delete_and_exists_passthrough() -> None:
    async def scenario() -> None:
        cache = DistributedCacheEngine(InMemoryCache())
        await cache.set("k", "v")
        assert await cache.exists("k") is True
        await cache.delete("k")
        assert await cache.exists("k") is False

    asyncio.run(scenario())
