import asyncio

import pytest

from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.ai_fabric.cache.engine import ResponseCache
from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.cost_optimizer.engine import CostOptimizer
from tmis.ai_fabric.latency_optimizer.engine import LatencyOptimizer
from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.quality_optimizer.engine import QualityOptimizer
from tmis.ai_fabric.quality_optimizer.store import InMemoryQualityStatsStore


def _model(name: str, *, cost: float, quality: float, available: bool = True) -> ModelDescriptor:
    return ModelDescriptor(
        name=name,
        version="1",
        provider="openai",
        cost_per_1k_tokens_usd=cost,
        avg_latency_ms=500.0,
        max_context_tokens=8_000,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
        profiles=frozenset({ModelProfile.DRAFTING}),
        availability=available,
        quality_score=quality,
    )


def test_cost_optimizer_picks_cheapest_model_meeting_quality_bar() -> None:
    optimizer = CostOptimizer()
    candidates = [
        _model("expensive", cost=0.05, quality=0.95),
        _model("cheap-and-good", cost=0.01, quality=0.85),
        _model("cheap-but-weak", cost=0.005, quality=0.4),
    ]

    best = optimizer.cheapest_meeting_quality(candidates, min_quality_score=0.8)

    assert best is not None
    assert best.name == "cheap-and-good"


def test_cost_optimizer_returns_none_when_nothing_meets_the_bar() -> None:
    optimizer = CostOptimizer()

    best = optimizer.cheapest_meeting_quality([_model("weak", cost=0.01, quality=0.2)], 0.9)

    assert best is None


def test_cost_optimizer_ignores_unavailable_models() -> None:
    optimizer = CostOptimizer()
    candidates = [_model("down", cost=0.001, quality=0.9, available=False)]

    assert optimizer.cheapest_meeting_quality(candidates, 0.5) is None


@pytest.mark.asyncio
async def test_cost_optimizer_try_cached_response_without_cache_returns_none() -> None:
    optimizer = CostOptimizer()

    assert await optimizer.try_cached_response("drafting", "gpt-x", "prompt") is None


@pytest.mark.asyncio
async def test_cost_optimizer_try_cached_response_with_cache() -> None:
    cache = ResponseCache(InMemoryCache())
    await cache.set("drafting", "gpt-x", "prompt", "cached response")
    optimizer = CostOptimizer(cache)

    result = await optimizer.try_cached_response("drafting", "gpt-x", "prompt")

    assert result == "cached response"


def test_latency_optimizer_fastest_available() -> None:
    optimizer = LatencyOptimizer()
    fast = ModelDescriptor(
        name="fast",
        version="1",
        provider="openai",
        cost_per_1k_tokens_usd=0.01,
        avg_latency_ms=100.0,
        max_context_tokens=8_000,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
    )
    slow = ModelDescriptor(
        name="slow",
        version="1",
        provider="openai",
        cost_per_1k_tokens_usd=0.01,
        avg_latency_ms=900.0,
        max_context_tokens=8_000,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
    )

    result = optimizer.fastest_available([slow, fast])
    assert result is not None
    assert result.name == "fast"


@pytest.mark.asyncio
async def test_latency_optimizer_run_parallel_respects_max_concurrency() -> None:
    optimizer = LatencyOptimizer(max_concurrency=2)
    concurrent = 0
    peak = 0

    async def _task() -> int:
        nonlocal concurrent, peak
        concurrent += 1
        peak = max(peak, concurrent)
        await asyncio.sleep(0.01)
        concurrent -= 1
        return 1

    results = await optimizer.run_parallel([_task() for _ in range(5)])

    assert results == [1, 1, 1, 1, 1]
    assert peak <= 2


@pytest.mark.asyncio
async def test_latency_optimizer_run_with_timeout_raises_on_expiry() -> None:
    optimizer = LatencyOptimizer(timeout_seconds=0.01)

    async def _slow() -> None:
        await asyncio.sleep(1)

    with pytest.raises(TimeoutError):
        await optimizer.run_with_timeout(_slow())


def test_quality_optimizer_tracks_error_rate() -> None:
    optimizer = QualityOptimizer(InMemoryQualityStatsStore())
    optimizer.record_call("gpt-x", success=True)
    optimizer.record_call("gpt-x", success=False)

    stats = optimizer.stats("gpt-x")

    assert stats.total_calls == 2
    assert stats.error_rate == 0.5
    assert stats.stability_score == 0.5


def test_quality_optimizer_average_feedback_defaults_to_neutral() -> None:
    optimizer = QualityOptimizer(InMemoryQualityStatsStore())

    assert optimizer.stats("unknown").average_feedback == 0.5


def test_quality_optimizer_leaderboard_orders_by_stability_then_feedback() -> None:
    optimizer = QualityOptimizer(InMemoryQualityStatsStore())
    optimizer.record_call("stable", success=True)
    optimizer.record_feedback("stable", 0.9)
    optimizer.record_call("flaky", success=False)

    leaderboard = optimizer.leaderboard()

    assert leaderboard[0].model_name == "stable"
