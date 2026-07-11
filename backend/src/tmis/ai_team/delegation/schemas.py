from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class DelegationRecord:
    """One "this sub-task went to this agent" decision (see
    docs/55-guide-coordinateur.md — Delegation). Append-only log used
    both for observability and for delegation tests."""

    mission_id: str
    sub_task_id: str
    agent_id: str | None
    delegated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
