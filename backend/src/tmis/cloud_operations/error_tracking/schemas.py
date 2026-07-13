import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ErrorSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def new_error_event_id() -> str:
    return f"err-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class ErrorEvent:
    """One tracked error, aggregated from any TMIS module — a workflow
    failure, an AI provider exception, a connector sync error — into a
    single cross-cutting error log."""

    id: str
    source: str
    error_type: str
    message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    firm_id: str | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
