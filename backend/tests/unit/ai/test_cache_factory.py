from collections.abc import Iterator

import pytest

from tmis.ai.cache import factory
from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.ai.cache.redis_cache import RedisCache
from tmis.core.config import Settings


class _StubRedisClient:
    """A fake `redis.asyncio.Redis` — enough for `RedisCache` construction
    without touching a socket."""


@pytest.fixture(autouse=True)
def _clear_singletons() -> Iterator[None]:
    factory._shared_redis_client.cache_clear()
    yield
    factory._shared_redis_client.cache_clear()


def test_defaults_to_in_memory_cache_when_redis_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())
    monkeypatch.setattr(factory, "_redis_reachable", lambda redis_url: False)

    cache = factory.make_cache()

    assert isinstance(cache, InMemoryCache)


def test_make_cache_returns_a_fresh_in_memory_instance_each_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every existing caller (`TMISKernel`, `BaseConnectorPlugin`,
    `ai_fabric.bootstrap.get_response_cache`) used to build its own
    `InMemoryCache()` — a private dict, never shared with another
    instance. Swapping in `make_cache()` must not silently start sharing
    that state (see `test_connector_search_uses_cache_on_second_call` in
    `tests/unit/platform_sdk/test_platform_sdk_agent_connector_sdk.py`,
    which would misfire if two connectors on the same `plugin_id` ever
    shared one dict).
    """
    monkeypatch.setattr(factory, "get_settings", lambda: Settings())
    monkeypatch.setattr(factory, "_redis_reachable", lambda redis_url: False)

    first = factory.make_cache()
    second = factory.make_cache()

    assert first is not second


def test_selects_redis_cache_when_redis_answers_a_ping(monkeypatch: pytest.MonkeyPatch) -> None:
    from redis.asyncio import Redis

    monkeypatch.setattr(factory, "get_settings", lambda: Settings())
    monkeypatch.setattr(factory, "_redis_reachable", lambda redis_url: True)
    monkeypatch.setattr(Redis, "from_url", lambda url, **kwargs: _StubRedisClient())

    cache = factory.make_cache()

    assert isinstance(cache, RedisCache)


def test_redis_reachability_is_probed_at_most_once_per_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from redis.asyncio import Redis

    calls: list[str] = []

    def _fake_reachable(redis_url: str) -> bool:
        calls.append(redis_url)
        return True

    monkeypatch.setattr(factory, "get_settings", lambda: Settings())
    monkeypatch.setattr(factory, "_redis_reachable", _fake_reachable)
    monkeypatch.setattr(Redis, "from_url", lambda url, **kwargs: _StubRedisClient())

    factory.make_cache()
    factory.make_cache()
    factory.make_cache()

    assert len(calls) == 1


def test_all_redis_cache_instances_share_the_one_client(monkeypatch: pytest.MonkeyPatch) -> None:
    from redis.asyncio import Redis

    monkeypatch.setattr(factory, "get_settings", lambda: Settings())
    monkeypatch.setattr(factory, "_redis_reachable", lambda redis_url: True)
    shared_client = _StubRedisClient()
    monkeypatch.setattr(Redis, "from_url", lambda url, **kwargs: shared_client)

    first = factory.make_cache()
    second = factory.make_cache()

    assert isinstance(first, RedisCache)
    assert isinstance(second, RedisCache)
    assert first._client is second._client is shared_client  # noqa: SLF001 — asserting the one-client invariant


def test_redis_reachable_never_raises_for_an_unroutable_url() -> None:
    """The real probe (not monkeypatched here): an unreachable/invalid
    Redis URL must degrade to `False`, never propagate an exception —
    this is what makes `make_cache()` safe to call unconditionally at
    startup with no Redis configured."""
    assert factory._redis_reachable("redis://127.0.0.1:1/0") is False  # noqa: SLF001


def test_make_cache_never_raises_with_default_settings_and_no_redis_running() -> None:
    """End-to-end proof of "jamais d'échec au démarrage si Redis est
    absent": with the real (unmonkeypatched) default `redis_url` and no
    Redis process listening in this test environment, `make_cache()`
    must still return a usable `CachePort`, never raise."""
    cache = factory.make_cache()

    assert isinstance(cache, InMemoryCache | RedisCache)
