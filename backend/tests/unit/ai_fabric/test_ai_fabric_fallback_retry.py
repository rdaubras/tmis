import pytest

from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.fallback.engine import FallbackEngine
from tmis.ai_fabric.fallback.schemas import NoAvailableModelError
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.model_registry.store import InMemoryModelRegistry
from tmis.ai_fabric.retry.engine import RetryPolicy


def _model(name: str, *, available: bool = True) -> ModelDescriptor:
    return ModelDescriptor(
        name=name,
        version="1",
        provider="openai",
        cost_per_1k_tokens_usd=0.01,
        avg_latency_ms=500.0,
        max_context_tokens=8_000,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
        availability=available,
    )


def test_fallback_resolves_primary_when_available() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("primary"))
    engine = FallbackEngine(registry)

    resolved = engine.resolve("primary", ("secondary",))

    assert resolved.name == "primary"
    assert engine.fallback_rate() == 0.0


def test_fallback_falls_back_when_primary_unavailable() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("primary", available=False))
    registry.register(_model("secondary"))
    engine = FallbackEngine(registry)

    resolved = engine.resolve("primary", ("secondary",))

    assert resolved.name == "secondary"
    assert engine.fallback_rate() == 1.0


def test_fallback_falls_back_when_primary_unregistered() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("secondary"))
    engine = FallbackEngine(registry)

    resolved = engine.resolve("missing", ("secondary",))

    assert resolved.name == "secondary"


def test_fallback_raises_when_no_model_is_available() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("primary", available=False))
    engine = FallbackEngine(registry)

    with pytest.raises(NoAvailableModelError):
        engine.resolve("primary", ())


def test_fallback_rate_is_zero_before_any_resolution() -> None:
    engine = FallbackEngine(InMemoryModelRegistry())

    assert engine.fallback_rate() == 0.0


@pytest.mark.asyncio
async def test_retry_policy_succeeds_on_first_attempt() -> None:
    policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.0)
    calls = 0

    async def _operation() -> str:
        nonlocal calls
        calls += 1
        return "ok"

    result = await policy.run(_operation)

    assert result == "ok"
    assert calls == 1


@pytest.mark.asyncio
async def test_retry_policy_retries_until_success() -> None:
    policy = RetryPolicy(max_attempts=3, base_delay_seconds=0.0)
    calls = 0

    async def _operation() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("transient failure")
        return "ok"

    result = await policy.run(_operation)

    assert result == "ok"
    assert calls == 3


@pytest.mark.asyncio
async def test_retry_policy_raises_after_exhausting_attempts() -> None:
    policy = RetryPolicy(max_attempts=2, base_delay_seconds=0.0)

    async def _operation() -> str:
        raise ValueError("persistent failure")

    with pytest.raises(ValueError, match="persistent failure"):
        await policy.run(_operation)
