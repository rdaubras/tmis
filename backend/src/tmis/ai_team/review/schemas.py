from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from tmis.ai_team.critique.schemas import Critique


class ReviewDecision(str, Enum):
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    """Ties a `Critique` into one reviewable decision per sub-task
    (see docs/57-guide-critique.md — Review). Feeds
    `tmis.ai_team.human_loop`: a human sees this record, not the raw
    critique, when deciding whether to approve a mission step."""

    mission_id: str
    sub_task_id: str
    critique: Critique
    decision: ReviewDecision
    reviewed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
