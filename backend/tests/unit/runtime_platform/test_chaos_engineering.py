import pytest

from tmis.cloud_operations.chaos_testing.engine import ProductionChaosTestingForbiddenError
from tmis.cloud_operations.resilience.engine import CircuitBreaker
from tmis.runtime_platform.chaos_engineering.engine import RuntimeChaosEngine
from tmis.runtime_platform.chaos_engineering.schemas import RuntimeChaosScenarioType


def _engine(environment: str = "development") -> tuple[RuntimeChaosEngine, CircuitBreaker]:
    breaker = CircuitBreaker()
    return RuntimeChaosEngine(environment, breaker), breaker


def test_run_scenario_forces_the_matching_circuit_open() -> None:
    engine, breaker = _engine()
    result = engine.run_scenario(RuntimeChaosScenarioType.NODE_LOSS)

    assert result.dependency == "runtime_platform.node"
    assert breaker.allow_request("runtime_platform.node") is False


def test_production_requires_explicit_authorization() -> None:
    engine, _ = _engine(environment="production")
    with pytest.raises(ProductionChaosTestingForbiddenError):
        engine.run_scenario(RuntimeChaosScenarioType.CACHE_LOSS)

    result = engine.run_scenario(RuntimeChaosScenarioType.CACHE_LOSS, authorized=True)
    assert result.dependency == "runtime_platform.cache"


def test_probe_counts_towards_availability_ratio() -> None:
    engine, breaker = _engine()
    engine.run_scenario(RuntimeChaosScenarioType.MESSAGE_BUS_LOSS)

    assert engine.probe(RuntimeChaosScenarioType.MESSAGE_BUS_LOSS) is False
    breaker.record_success("runtime_platform.event_bus")
    assert engine.probe(RuntimeChaosScenarioType.MESSAGE_BUS_LOSS) is True


def test_measure_recovery_requires_the_dependency_to_be_available_again() -> None:
    engine, breaker = _engine()
    engine.run_scenario(RuntimeChaosScenarioType.NODE_LOSS)

    with pytest.raises(RuntimeError):
        engine.measure_recovery(RuntimeChaosScenarioType.NODE_LOSS)

    breaker.record_success("runtime_platform.node")
    result = engine.measure_recovery(RuntimeChaosScenarioType.NODE_LOSS, item_loss_count=2)
    assert result.recovery_time_seconds is not None
    assert result.recovery_time_seconds >= 0
    assert result.item_loss_count == 2


def test_measure_recovery_of_unknown_run_raises_key_error() -> None:
    engine, _ = _engine()
    with pytest.raises(KeyError):
        engine.measure_recovery(RuntimeChaosScenarioType.CACHE_LOSS)
