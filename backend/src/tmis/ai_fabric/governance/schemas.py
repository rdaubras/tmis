import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_decision_id() -> str:
    return f"gov-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    id: str
    firm_id: str
    model_name: str
    allowed: bool
    reasons: tuple[str, ...]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
