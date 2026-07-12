"""Standalone event hierarchy for the Legal Integration Hub.

Deliberately its own hierarchy — mirrors
`tmis.collaboration.event_bus.CollaborationEvent`,
`tmis.ai_governance.events.GovernanceEvent`, and
`tmis.workflow_automation.event_bus.WorkflowEvent` — rather than
sharing any of them. `EventBridge` is the one place that explicitly
translates between this hierarchy and `WorkflowEvent`.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class EventDirection(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


@dataclass(frozen=True, kw_only=True)
class IntegrationEvent:
    firm_id: str
    connector_id: str
    direction: EventDirection
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def event_type(self) -> str:
        return type(self).__name__


@dataclass(frozen=True, kw_only=True)
class ExternalRecordChanged(IntegrationEvent):
    """An inbound change notification from a connector — webhook
    payload or poll-detected diff."""

    entity_type: str
    external_id: str
    payload: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, kw_only=True)
class SyncCompleted(IntegrationEvent):
    job_id: str
    records_written: int
    conflicts: int


@dataclass(frozen=True, kw_only=True)
class ConnectorAuthFailed(IntegrationEvent):
    detail: str


@dataclass(frozen=True, kw_only=True)
class OutboundNotificationRequested(IntegrationEvent):
    """A TMIS-side change to be pushed out to the external system."""

    entity_type: str
    external_id: str
    payload: dict[str, str] = field(default_factory=dict)
