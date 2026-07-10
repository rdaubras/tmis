from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ActivityType(str, Enum):
    """The journal categories called out in the sprint brief: imports,
    modifications, comments, validations, tasks, AI research, AI
    generation — plus MEMBER/WORKSPACE for collaboration lifecycle
    events, so the feed covers everything LCE itself emits."""

    IMPORT = "import"
    MODIFICATION = "modification"
    COMMENT = "comment"
    APPROVAL = "approval"
    TASK = "task"
    AI_RESEARCH = "ai_research"
    AI_GENERATION = "ai_generation"
    MEMBER = "member"
    WORKSPACE = "workspace"
    SHARING = "sharing"


@dataclass(frozen=True, slots=True)
class ActivityEntry:
    id: str
    workspace_id: str
    actor_id: str
    activity_type: ActivityType
    target_type: str
    target_id: str
    summary: str
    occurred_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)
