from datetime import UTC, datetime

from tmis.cloud_operations.chaos_testing.engine import ensure_chaos_authorized
from tmis.cloud_operations.resilience.engine import CircuitBreaker
from tmis.runtime_platform.chaos_engineering.schemas import (
    RuntimeChaosResult,
    RuntimeChaosScenarioType,
)

_DEPENDENCY_FOR_SCENARIO: dict[RuntimeChaosScenarioType, str] = {
    RuntimeChaosScenarioType.NODE_LOSS: "runtime_platform.node",
    RuntimeChaosScenarioType.CACHE_LOSS: "runtime_platform.cache",
    RuntimeChaosScenarioType.MESSAGE_BUS_LOSS: "runtime_platform.event_bus",
}


class RuntimeChaosEngine:
    """Extends `cloud_operations.chaos_testing.ChaosTestingEngine`'s
    approach (force a named `CircuitBreaker` circuit open to simulate
    an outage, guarded by the same production-authorization check —
    reused via `ensure_chaos_authorized`, not re-derived) with three
    additional scenarios and automatic measurement of recovery time,
    availability, and item loss during the outage — which the
    Sprint 21 engine does not compute; it only reports that a circuit
    was forced open."""

    def __init__(self, environment: str, resilience: CircuitBreaker) -> None:
        self._environment = environment
        self._resilience = resilience
        self._active: dict[RuntimeChaosScenarioType, RuntimeChaosResult] = {}

    def run_scenario(
        self, scenario: RuntimeChaosScenarioType, *, authorized: bool = False
    ) -> RuntimeChaosResult:
        ensure_chaos_authorized(self._environment, authorized, scenario.value)
        dependency = _DEPENDENCY_FOR_SCENARIO[scenario]
        self._resilience.force_open(dependency)
        result = RuntimeChaosResult(
            scenario=scenario, dependency=dependency, opened_at=datetime.now(UTC)
        )
        self._active[scenario] = result
        return result

    def probe(self, scenario: RuntimeChaosScenarioType) -> bool:
        """Simulates a health check against the affected dependency
        during the outage — each call is one availability sample."""
        result = self._require_active(scenario)
        dependency = _DEPENDENCY_FOR_SCENARIO[scenario]
        result.probes_total += 1
        ok = self._resilience.allow_request(dependency)
        if ok:
            result.probes_successful += 1
        return ok

    def measure_recovery(
        self, scenario: RuntimeChaosScenarioType, *, item_loss_count: int = 0
    ) -> RuntimeChaosResult:
        """Call once the dependency's circuit has closed again
        (either because `recovery_timeout_seconds` elapsed and a
        probe succeeded, or because a caller simulated real recovery
        via `CircuitBreaker.record_success`) to finalize the
        measurement."""
        result = self._require_active(scenario)
        dependency = _DEPENDENCY_FOR_SCENARIO[scenario]
        if not self._resilience.allow_request(dependency):
            raise RuntimeError(f"{scenario.value} has not recovered yet")
        now = datetime.now(UTC)
        result.recovered_at = now
        result.recovery_time_seconds = (now - result.opened_at).total_seconds()
        result.item_loss_count = item_loss_count
        del self._active[scenario]
        return result

    def _require_active(self, scenario: RuntimeChaosScenarioType) -> RuntimeChaosResult:
        result = self._active.get(scenario)
        if result is None:
            raise KeyError(f"no active chaos run for {scenario.value}")
        return result
