import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_rollback_log_id() -> str:
    return f"rollback-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class RollbackResult:
    compensated: bool
    detail: str


@dataclass(frozen=True, slots=True)
class RollbackLogEntry:
    """Every rollback attempt is journaled, successful or not — same
    "always journaled" convention as `action_engine.ActionLogEntry`."""

    id: str
    firm_id: str
    execution_id: str
    action_id: str
    action_type: str
    result: RollbackResult
    executed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
