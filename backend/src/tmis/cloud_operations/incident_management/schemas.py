import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class IncidentStatus(StrEnum):
    """The four lifecycle stages the sprint asks for ("ouverture,
    suivi, résolution, post-mortem"), plus a terminal CLOSED state
    reached once the post-mortem has been recorded."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    POST_MORTEM = "post_mortem"
    CLOSED = "closed"


class IncidentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def new_incident_id() -> str:
    return f"inc-{uuid.uuid4().hex[:12]}"


def new_incident_update_id() -> str:
    return f"incu-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class IncidentUpdate:
    """One timeline entry in an incident's tracking log."""

    id: str
    incident_id: str
    message: str
    author: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Incident:
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.OPEN
    firm_id: str | None = None
    opened_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    resolved_at: datetime | None = None
    post_mortem: str | None = None


@dataclass(frozen=True, slots=True)
class PostMortemReport:
    """The report template the sprint asks for ("modèles de
    rapport") — a fixed structure every post-mortem fills in."""

    incident_id: str
    title: str
    severity: IncidentSeverity
    summary: str
    root_cause: str
    impact: str
    resolution: str
    action_items: list[str]
    duration_minutes: float
