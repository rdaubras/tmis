from collections.abc import Iterator

import pytest

from tmis.ai.cache import factory as cache_factory
from tmis.ai.memory import factory as memory_factory
from tmis.ai.memory.in_memory_store import InMemoryStore
from tmis.ai.memory.redis_store import RedisMemoryStore
from tmis.core.config import Settings


class _StubRedisClient:
    """A fake `redis.asyncio.Redis` — enough for `RedisMemoryStore`
    construction without touching a socket."""


@pytest.fixture(autouse=True)
def _clear_singletons() -> Iterator[None]:
    cache_factory._shared_redis_client.cache_clear()  # noqa: SLF001
    yield
    cache_factory._shared_redis_client.cache_clear()  # noqa: SLF001


def test_defaults_to_in_memory_store_when_redis_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(cache_factory, "get_settings", lambda: Settings())
    monkeypatch.setattr(cache_factory, "_redis_reachable", lambda redis_url: False)

    store = memory_factory.make_memory_store()

    assert isinstance(store, InMemoryStore)


def test_selects_redis_memory_store_when_redis_answers_a_ping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from redis.asyncio import Redis

    monkeypatch.setattr(cache_factory, "get_settings", lambda: Settings())
    monkeypatch.setattr(cache_factory, "_redis_reachable", lambda redis_url: True)
    monkeypatch.setattr(Redis, "from_url", lambda url, **kwargs: _StubRedisClient())

    store = memory_factory.make_memory_store()

    assert isinstance(store, RedisMemoryStore)


def test_memory_store_and_cache_share_the_one_redis_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The repo's single Redis connection mechanism: `make_memory_store()`
    must reuse `cache.factory._shared_redis_client()`, never dial a
    second connection."""
    from redis.asyncio import Redis

    from tmis.ai.cache.factory import make_cache
    from tmis.ai.cache.redis_cache import RedisCache

    monkeypatch.setattr(cache_factory, "get_settings", lambda: Settings())
    monkeypatch.setattr(cache_factory, "_redis_reachable", lambda redis_url: True)
    shared_client = _StubRedisClient()
    monkeypatch.setattr(Redis, "from_url", lambda url, **kwargs: shared_client)

    cache = make_cache()
    store = memory_factory.make_memory_store()

    assert isinstance(cache, RedisCache)
    assert isinstance(store, RedisMemoryStore)
    assert cache._client is store._client is shared_client  # noqa: SLF001


def test_make_memory_store_never_raises_with_default_settings_and_no_redis_running() -> None:
    """End-to-end proof of "jamais d'échec au démarrage si Redis est
    absent", same standard as `test_cache_factory.
    test_make_cache_never_raises_with_default_settings_and_no_redis_running`."""
    store = memory_factory.make_memory_store()

    assert isinstance(store, InMemoryStore | RedisMemoryStore)
