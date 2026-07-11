import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.workflow_automation.condition_engine.schemas import Condition


def new_rule_id() -> str:
    return f"rule-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class Rule:
    """A configurable rule — "les règles sont configurables sans
    modification du code" (sprint requirement). `condition` may
    reference case data, user role, procedure type, workflow state or
    AI policies; all of those are assembled by the caller into the
    evaluation context, keeping this engine free of cross-context
    imports."""

    id: str
    firm_id: str
    name: str
    condition: Condition
    description: str = ""
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
