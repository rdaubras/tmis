import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class MeteredDimension(StrEnum):
    """The seven metered signals the sprint asks for — "appels IA,
    tokens consommés, stockage utilisé, documents générés, workflows
    exécutés, recherches, connecteurs actifs"."""

    AI_CALLS = "ai_calls"
    TOKENS = "tokens"
    STORAGE_GB = "storage_gb"
    DOCUMENTS_GENERATED = "documents_generated"
    WORKFLOWS_EXECUTED = "workflows_executed"
    SEARCHES = "searches"
    ACTIVE_CONNECTORS = "active_connectors"


def new_event_id() -> str:
    return f"meter-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class MeteringEvent:
    """One metered occurrence — "toutes les métriques sont
    historisées" (sprint requirement): events are append-only, never
    updated or deleted, so a firm's consumption history is always
    reconstructible from the raw event log rather than a mutable
    running counter."""

    id: str
    firm_id: str
    dimension: MeteredDimension
    quantity: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = field(default_factory=dict)
