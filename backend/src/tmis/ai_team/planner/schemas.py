import uuid
from dataclasses import dataclass, field

from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.capabilities.schemas import TaskType


@dataclass(frozen=True, slots=True)
class SubTask:
    """One step of a decomposed mission (see
    docs/55-guide-coordinateur.md — Planner). `depends_on` lists the
    ids of sub-tasks that must complete before this one can start —
    the Coordinator/WorkQueue use this to sequence delegation without
    the Planner itself running anything."""

    id: str
    task_type: TaskType
    assigned_role: AgentRole
    description: str
    depends_on: tuple[str, ...] = ()


def new_subtask_id() -> str:
    return str(uuid.uuid4())


@dataclass(frozen=True, slots=True)
class MissionPlan:
    sub_tasks: list[SubTask] = field(default_factory=list)
