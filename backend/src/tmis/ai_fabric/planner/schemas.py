from dataclasses import dataclass, field
from enum import StrEnum

from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.router.schemas import RoutingDecision


class PlanStepKind(StrEnum):
    ROUTE = "route"
    CRITIQUE = "critique"


@dataclass(frozen=True, slots=True)
class SubTask:
    name: str
    kind: PlanStepKind
    profile: ModelProfile | None = None


@dataclass(frozen=True, slots=True)
class PlannedStep:
    sub_task: SubTask
    decision: RoutingDecision | None = None


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    task_description: str
    steps: tuple[PlannedStep, ...] = field(default_factory=tuple)
