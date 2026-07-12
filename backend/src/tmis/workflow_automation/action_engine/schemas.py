import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

# Free-form action types the sprint names explicitly — new types are
# added by registering a new `ActionHandlerPort`, never by editing
# this module (the sprint's "toutes les automatisations doivent être
# configurables" requirement extends to actions themselves).
ACTION_CREATE_TASK = "create_task"
ACTION_NOTIFY = "notify"
ACTION_LAUNCH_AI_ANALYSIS = "launch_ai_analysis"
ACTION_GENERATE_DRAFT = "generate_draft"
ACTION_ENRICH_KNOWLEDGE = "enrich_knowledge"
ACTION_CREATE_REMINDER = "create_reminder"
ACTION_CALL_INTEGRATION = "call_integration"


def new_action_id() -> str:
    return f"action-{uuid.uuid4().hex[:12]}"


def new_action_log_id() -> str:
    return f"action-log-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class Action:
    id: str
    workflow_id: str
    action_type: str
    config: dict[str, str] = field(default_factory=dict)
    requires_approval: bool = False


@dataclass(frozen=True, slots=True)
class ActionResult:
    success: bool
    detail: str
    output: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ActionLogEntry:
    """Every action execution is journaled — "toutes les actions sont
    journalisées" (sprint requirement) — never silently dropped, even
    on failure."""

    id: str
    firm_id: str
    execution_id: str
    action_id: str
    action_type: str
    result: ActionResult
    executed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
