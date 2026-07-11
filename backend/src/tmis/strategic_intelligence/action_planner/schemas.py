import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_action_step_id() -> str:
    return f"action-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class ActionStep:
    """One step of a strategy's action plan. Fully mutable and
    reorderable by the user — "le plan reste entièrement modifiable par
    l'utilisateur" (sprint requirement) — unlike the append-only,
    state-machine-governed objects elsewhere in this sprint."""

    id: str
    strategy_id: str
    description: str
    category: str
    order: int
    done: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
