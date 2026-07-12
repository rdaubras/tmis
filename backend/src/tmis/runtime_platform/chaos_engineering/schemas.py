from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RuntimeChaosScenarioType(StrEnum):
    """Three of the five failure types this sprint asks for beyond
    `cloud_operations.chaos_testing.ChaosScenarioType`'s existing
    four ("panne fournisseur IA" = `AI_PROVIDER_OUTAGE`, "perte d'une
    intégration" = `NETWORK_CUT`, both already covered — extended
    here, not duplicated, with "perte d'un nœud, perte du cache,
    perte du Message Bus")."""

    NODE_LOSS = "node_loss"
    CACHE_LOSS = "cache_loss"
    MESSAGE_BUS_LOSS = "message_bus_loss"


@dataclass(slots=True)
class RuntimeChaosResult:
    scenario: RuntimeChaosScenarioType
    dependency: str
    opened_at: datetime
    recovered_at: datetime | None = None
    recovery_time_seconds: float | None = None
    probes_total: int = 0
    probes_successful: int = 0
    item_loss_count: int = 0
    measured_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def availability_ratio(self) -> float:
        if self.probes_total == 0:
            return 0.0
        return self.probes_successful / self.probes_total
