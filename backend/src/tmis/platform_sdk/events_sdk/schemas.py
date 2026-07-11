import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class PlatformEventName(StrEnum):
    """The canonical, documented event names (see the sprint's "EVENT
    SDK" spec) — the bus itself is not limited to these (see
    `PlatformEventBus.publish`'s `event_name: str` parameter), so a
    plugin can define and publish its own event names too ("le
    système doit être extensible")."""

    DOCUMENT_UPLOADED = "DocumentUploaded"
    CASE_UPDATED = "CaseUpdated"
    DRAFT_GENERATED = "DraftGenerated"
    KNOWLEDGE_VALIDATED = "KnowledgeValidated"
    TASK_COMPLETED = "TaskCompleted"
    AI_WORKFLOW_FINISHED = "AIWorkflowFinished"


@dataclass(frozen=True, kw_only=True, slots=True)
class PlatformEvent:
    """A standalone event type for `tmis.platform_sdk`, deliberately
    **not** a subclass of `tmis.ai.events.Event` (Kernel-specific,
    requires `workflow_id`) nor imported from
    `tmis.collaboration.CollaborationEvent` — each bounded context
    gets its own `Event`/`EventBus` pair with zero cross-import, the
    convention `tmis.collaboration` established in Sprint 8."""

    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    event_name: str
    source_context: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
