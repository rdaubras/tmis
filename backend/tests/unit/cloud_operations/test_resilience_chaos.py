import asyncio

import pytest

from tmis.cloud_operations.chaos_testing.engine import (
    ChaosTestingEngine,
    ProductionChaosTestingForbiddenError,
)
from tmis.cloud_operations.chaos_testing.schemas import ChaosScenarioType
from tmis.cloud_operations.resilience.engine import CircuitBreaker, CircuitOpenError
from tmis.cloud_operations.resilience.schemas import CircuitBreakerConfig, CircuitState


async def _failing() -> str:
    raise RuntimeError("boom")


async def _ok() -> str:
    return "ok"


def test_circuit_breaker_opens_after_threshold_and_recovers() -> None:
    async def scenario() -> None:
        breaker = CircuitBreaker(
            CircuitBreakerConfig(failure_threshold=2, recovery_timeout_seconds=0.05)
        )
        for _ in range(2):
            with pytest.raises(RuntimeError):
                await breaker.call("svc", _failing)
        assert breaker.state("svc").state is CircuitState.OPEN

        with pytest.raises(CircuitOpenError):
            await breaker.call("svc", _ok)

        await asyncio.sleep(0.06)
        result = await breaker.call("svc", _ok)
        assert result == "ok"
        assert breaker.state("svc").state is CircuitState.CLOSED

    asyncio.run(scenario())


def test_circuit_breaker_force_open_bypasses_threshold() -> None:
    breaker = CircuitBreaker()
    state = breaker.force_open("ai_fabric.provider")
    assert state.state is CircuitState.OPEN
    assert breaker.allow_request("ai_fabric.provider") is False


def test_chaos_testing_simulates_all_four_scenarios_in_dev() -> None:
    breaker = CircuitBreaker()
    engine = ChaosTestingEngine("development", breaker)
    for scenario in ChaosScenarioType:
        result = engine.run_scenario(scenario)
        assert result.scenario is scenario


def test_chaos_testing_forbidden_in_production_without_authorization() -> None:
    engine = ChaosTestingEngine("production", CircuitBreaker())
    with pytest.raises(ProductionChaosTestingForbiddenError):
        engine.run_scenario(ChaosScenarioType.DATABASE_UNAVAILABLE)

    result = engine.run_scenario(ChaosScenarioType.DATABASE_UNAVAILABLE, authorized=True)
    assert result.scenario is ChaosScenarioType.DATABASE_UNAVAILABLE
