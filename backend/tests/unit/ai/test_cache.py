import pytest

from tmis.ai.cache.in_memory_cache import InMemoryCache


@pytest.mark.asyncio
async def test_get_missing_key_returns_none() -> None:
    cache = InMemoryCache()
    assert await cache.get("missing") is None


@pytest.mark.asyncio
async def test_set_then_get_roundtrips() -> None:
    cache = InMemoryCache()
    await cache.set("key", "value")
    assert await cache.get("key") == "value"
    assert await cache.exists("key") is True


@pytest.mark.asyncio
async def test_delete_removes_key() -> None:
    cache = InMemoryCache()
    await cache.set("key", "value")
    await cache.delete("key")
    assert await cache.get("key") is None
    assert await cache.exists("key") is False


@pytest.mark.asyncio
async def test_ttl_expiry(monkeypatch: pytest.MonkeyPatch) -> None:
    import time

    cache = InMemoryCache()
    fake_clock = {"t": 1000.0}
    monkeypatch.setattr(time, "monotonic", lambda: fake_clock["t"])

    await cache.set("key", "value", ttl_seconds=10)
    fake_clock["t"] += 11

    assert await cache.get("key") is None
