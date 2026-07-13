from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ChaosScenarioType(StrEnum):
    """The four failure types the sprint asks the resilience tests to
    simulate ("panne fournisseur IA, indisponibilité base de données,
    coupure réseau, saturation de file d'attente")."""

    AI_PROVIDER_OUTAGE = "ai_provider_outage"
    DATABASE_UNAVAILABLE = "database_unavailable"
    NETWORK_CUT = "network_cut"
    QUEUE_SATURATION = "queue_saturation"


@dataclass(frozen=True, slots=True)
class ChaosScenarioResult:
    scenario: ChaosScenarioType
    detail: str
    executed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
