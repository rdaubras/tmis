"""Standalone event hierarchy for the Autonomous Legal Workflow Platform.

Deliberately its own hierarchy — mirrors
`tmis.collaboration.event_bus.CollaborationEvent` and
`tmis.ai_governance.events.GovernanceEvent` — rather than sharing
`tmis.ai.events` or importing from another bounded context. Any
business module that wants to trigger a workflow publishes one of
these events on `WorkflowEventBus`; `trigger_engine` is the only
subscriber this package defines.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, kw_only=True)
class WorkflowEvent:
    firm_id: str
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        return type(self).__name__


@dataclass(frozen=True, kw_only=True)
class BusinessEventOccurred(WorkflowEvent):
    """A domain event from any other bounded context (document
    imported, hearing created, draft validated...) re-published here
    as a generic, workflow-triggerable event."""

    source: str
    label: str
    payload: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class DeadlineApproaching(WorkflowEvent):
    case_id: str
    deadline_label: str
    days_remaining: int


@dataclass(frozen=True, kw_only=True)
class DocumentCreated(WorkflowEvent):
    case_id: str
    document_id: str
    document_type: str


@dataclass(frozen=True, kw_only=True)
class CaseUpdated(WorkflowEvent):
    case_id: str
    field_changed: str


@dataclass(frozen=True, kw_only=True)
class ValidationCompleted(WorkflowEvent):
    target_type: str
    target_id: str
    approved: bool


@dataclass(frozen=True, kw_only=True)
class IntegrationEventReceived(WorkflowEvent):
    integration_name: str
    label: str
    payload: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class WorkflowExecutionStarted(WorkflowEvent):
    workflow_id: str
    execution_id: str


@dataclass(frozen=True, kw_only=True)
class WorkflowExecutionCompleted(WorkflowEvent):
    workflow_id: str
    execution_id: str


@dataclass(frozen=True, kw_only=True)
class WorkflowExecutionFailed(WorkflowEvent):
    workflow_id: str
    execution_id: str
    reason: str
