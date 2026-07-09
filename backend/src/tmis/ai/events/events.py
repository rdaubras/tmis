import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, kw_only=True)
class Event:
    """Base class for every event exchanged on the `EventBus`."""

    workflow_id: uuid.UUID
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        return type(self).__name__


@dataclass(frozen=True, kw_only=True)
class UserQuestionReceived(Event):
    question: str


@dataclass(frozen=True, kw_only=True)
class WorkflowStarted(Event):
    workflow_name: str


@dataclass(frozen=True, kw_only=True)
class ResearchCompleted(Event):
    result_count: int


@dataclass(frozen=True, kw_only=True)
class DraftGenerated(Event):
    draft_id: str


@dataclass(frozen=True, kw_only=True)
class VerificationCompleted(Event):
    warning_count: int


@dataclass(frozen=True, kw_only=True)
class WorkflowFinished(Event):
    workflow_name: str
    success: bool
