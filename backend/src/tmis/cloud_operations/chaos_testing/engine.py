from tmis.cloud_operations.chaos_testing.schemas import ChaosScenarioResult, ChaosScenarioType
from tmis.cloud_operations.resilience.engine import CircuitBreaker

_DEPENDENCY_FOR_SCENARIO: dict[ChaosScenarioType, str] = {
    ChaosScenarioType.AI_PROVIDER_OUTAGE: "ai_fabric.provider",
    ChaosScenarioType.DATABASE_UNAVAILABLE: "platform.database",
    ChaosScenarioType.NETWORK_CUT: "integration_hub.connector",
    ChaosScenarioType.QUEUE_SATURATION: "cloud_operations.queue",
}


class ProductionChaosTestingForbiddenError(RuntimeError):
    """Raised when a chaos scenario is requested against a production
    environment without explicit authorization — the sprint's hard
    safety constraint ("ces tests ne doivent jamais s'exécuter en
    production sans autorisation explicite")."""


class ChaosTestingEngine:
    """Resilience test architecture simulating the four failure types
    the sprint asks for. Each scenario forces the matching named
    circuit in `resilience.CircuitBreaker` open, so a caller can
    observe how the rest of the system behaves under that dependency
    being unavailable — a simulation, not real infrastructure
    disruption, so it is safe to run repeatedly in any non-production
    environment."""

    def __init__(self, environment: str, resilience: CircuitBreaker) -> None:
        self._environment = environment
        self._resilience = resilience

    def run_scenario(
        self, scenario: ChaosScenarioType, *, authorized: bool = False
    ) -> ChaosScenarioResult:
        if self._environment == "production" and not authorized:
            raise ProductionChaosTestingForbiddenError(scenario.value)
        dependency = _DEPENDENCY_FOR_SCENARIO[scenario]
        self._resilience.force_open(dependency)
        detail = f"Forced circuit '{dependency}' open to simulate {scenario.value}"
        return ChaosScenarioResult(scenario=scenario, detail=detail)
