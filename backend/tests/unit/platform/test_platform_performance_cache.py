import asyncio

import pytest

from tmis.platform.cache.policy import CachePolicyRegistry
from tmis.platform.performance.benchmark import benchmark
from tmis.platform.performance.concurrency import bounded_gather
from tmis.platform.performance.pagination import Page, PageRequest, paginate


def test_page_request_clamps_oversized_page_size() -> None:
    request = PageRequest(page=1, page_size=10_000)

    assert request.page_size == 200


def test_page_request_rejects_non_positive_page() -> None:
    with pytest.raises(ValueError):
        PageRequest(page=0)


def test_page_request_rejects_non_positive_page_size() -> None:
    with pytest.raises(ValueError):
        PageRequest(page=1, page_size=0)


def test_page_request_offset_is_zero_indexed() -> None:
    request = PageRequest(page=3, page_size=10)

    assert request.offset == 20


def test_paginate_slices_correctly_and_reports_total() -> None:
    items = list(range(25))

    page = paginate(items, PageRequest(page=2, page_size=10))

    assert page.items == list(range(10, 20))
    assert page.total == 25
    assert page.has_next is True
    assert page.has_previous is True


def test_page_has_next_is_false_on_the_last_page() -> None:
    page: Page[int] = Page(items=[9], total=10, page=10, page_size=1)

    assert page.has_next is False


def test_benchmark_reports_iteration_count_and_stats() -> None:
    result = benchmark("noop", lambda: None, iterations=10)

    assert result.iterations == 10
    assert result.mean_ms >= 0.0
    assert result.min_ms <= result.mean_ms <= result.max_ms


def test_cache_policy_registry_returns_configured_ttl() -> None:
    registry = CachePolicyRegistry()

    assert registry.get_ttl("kernel_completion") == 3600


def test_cache_policy_registry_returns_default_for_unknown_resource() -> None:
    registry = CachePolicyRegistry()

    assert registry.get_ttl("unknown_resource", default=42) == 42


def test_cache_policy_registry_set_ttl_overrides_default() -> None:
    registry = CachePolicyRegistry()
    registry.set_ttl("kernel_completion", 60)

    assert registry.get_ttl("kernel_completion") == 60


async def test_bounded_gather_runs_every_coroutine_and_preserves_order() -> None:
    async def _identity(value: int) -> int:
        await asyncio.sleep(0)
        return value

    results = await bounded_gather([_identity(i) for i in range(20)], max_concurrency=3)

    assert results == list(range(20))


async def test_bounded_gather_never_exceeds_max_concurrency() -> None:
    active = 0
    peak = 0

    async def _tracked() -> None:
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0.01)
        active -= 1

    await bounded_gather([_tracked() for _ in range(20)], max_concurrency=4)

    assert peak <= 4
