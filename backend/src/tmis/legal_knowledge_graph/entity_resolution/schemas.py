import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ResolutionStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


def new_resolution_match_id() -> str:
    return f"resmatch-{uuid.uuid4()}"


@dataclass(slots=True)
class ResolutionMatch:
    """A proposed "these two graph nodes are the same real-world
    entity" — scoring plus a human decision, exactly as the sprint
    asks ("prévoir : scoring, validation humaine, historique"). Never
    overwritten in place by the store; `decide()` appends a new
    record so the full history of a match is always available."""

    id: str
    firm_id: str
    node_id_a: str
    node_id_b: str
    score: float
    status: ResolutionStatus = ResolutionStatus.PENDING
    decided_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
