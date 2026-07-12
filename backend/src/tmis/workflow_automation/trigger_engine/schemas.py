from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum


class TriggerType(StrEnum):
    BUSINESS_EVENT = "business_event"
    SCHEDULE = "schedule"
    DEADLINE = "deadline"
    DOCUMENT_CREATED = "document_created"
    CASE_UPDATED = "case_updated"
    VALIDATION = "validation"
    INTEGRATION_EVENT = "integration_event"


def new_trigger_id() -> str:
    return f"trigger-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class Trigger:
    """One condition under which a workflow should fire. `config` is a
    free-form string map interpreted by the matching
    `TriggerMatcherPort` — new trigger types are added by registering a
    new matcher, never by editing this schema (the sprint's "le système
    doit être extensible" requirement)."""

    id: str
    workflow_id: str
    trigger_type: TriggerType
    config: dict[str, str] = field(default_factory=dict)
