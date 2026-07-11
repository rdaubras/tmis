import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_decision_record_id() -> str:
    return f"dec-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    """The sprint's "DECISION RECORDS" spec: contexte, objectif,
    hypothèses, alternatives envisagées, décision retenue,
    justification, impacts — historized, never mutated in place."""

    id: str
    firm_id: str
    production_id: str
    context: str
    objective: str
    hypotheses_considered: tuple[str, ...]
    alternatives_considered: tuple[str, ...]
    decision: str
    justification: str
    impacts: tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
