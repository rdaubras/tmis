from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(slots=True)
class EventEnvelope:
    """Wraps one event published through an `EventStreamingEngine`,
    adding the four capabilities the Sprint 23 Phase 1 audit
    confirmed were missing from all seven existing in-memory event
    buses (`ai.events.EventBus`, `workflow_automation.event_bus.
    WorkflowEventBus`, `collaboration.CollaborationEventBus`,
    `identity_platform.security_events.SecurityEventBus`,
    `integration_hub.event_bridge.IntegrationEventBus`,
    `platform_sdk.events_sdk.PlatformEventBus`,
    `ai_governance.events.GovernanceEventBus`): a monotonic
    `sequence` (ordering), a `version` tag (versioning), and an
    optional `idempotency_key` the engine deduplicates on. Wrapping,
    not replacing — the underlying bus still owns delivery to its own
    subscribers."""

    sequence: int
    event: object
    event_type: str
    version: int
    idempotency_key: str | None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    archived: bool = False
