from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from tmis.ai.schemas.agent import AgentOutput
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.ai_team.planner.schemas import MissionPlan


class MissionStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    AWAITING_HUMAN_REVIEW = "awaiting_human_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class Mission:
    """A mission is the Coordinator's unit of work: one request, one
    plan, one team, tracked end to end (see
    docs/55-guide-coordinateur.md). `results` is keyed by sub-task id;
    `synthesis` is produced structurally by the Coordinator itself —
    it never runs an analysis of its own (see the sprint constraint)."""

    id: str
    firm_id: str
    request_description: str
    domain: LegalDomain
    team_id: str
    plan: MissionPlan
    status: MissionStatus = MissionStatus.CREATED
    work_item_ids: list[str] = field(default_factory=list)
    results: dict[str, AgentOutput] = field(default_factory=dict)
    synthesis: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
