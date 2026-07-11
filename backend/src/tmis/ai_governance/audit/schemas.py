import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_ai_audit_entry_id() -> str:
    return f"aiaudit-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class AIAuditEntry:
    """The sprint's specialized AI audit journal: prompts, modèles,
    coûts, temps, décisions, politiques appliquées, validations — a
    distinct concept from `tmis.collaboration.audit.AuditEntry`
    (generic workspace activity) and
    `tmis.platform.compliance.schemas.AccessLogEntry` (personal-data
    access), scoped to AI production activity specifically."""

    id: str
    firm_id: str
    production_id: str
    actor_id: str
    action: str
    prompt: str | None = None
    model_name: str | None = None
    cost_usd: float | None = None
    duration_ms: float | None = None
    decision_id: str | None = None
    policy_ids: tuple[str, ...] = field(default_factory=tuple)
    validation_id: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
