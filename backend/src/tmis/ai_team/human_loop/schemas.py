import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum


class HumanDecisionType(str, Enum):
    APPROVE = "approve"
    REQUEST_NEW_ANALYSIS = "request_new_analysis"
    EXCLUDE_AGENT = "exclude_agent"
    ADD_AGENT = "add_agent"
    MODIFY_PLAN = "modify_plan"
    RERUN_STEPS = "rerun_steps"


@dataclass(frozen=True, slots=True)
class HumanDecision:
    """One human decision on a mission (see
    docs/55-guide-coordinateur.md — Human in the Loop). Every decision
    is historized here — never overwritten, never deleted — so the
    full trail of who decided what, and when, survives independently
    of the mission's own mutable state."""

    id: str
    mission_id: str
    actor_id: str
    decision_type: HumanDecisionType
    payload: dict[str, str] = field(default_factory=dict)
    decided_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def new_decision_id() -> str:
    return str(uuid.uuid4())
