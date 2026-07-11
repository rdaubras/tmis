from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.planner.schemas import ExecutionPlan, PlannedStep, PlanStepKind, SubTask
from tmis.ai_fabric.router.engine import RouterEngine
from tmis.ai_fabric.router.schemas import RoutingRequest

DEFAULT_PIPELINE: tuple[SubTask, ...] = (
    SubTask("Analyse documentaire", PlanStepKind.ROUTE, ModelProfile.VISION),
    SubTask("Extraction", PlanStepKind.ROUTE, ModelProfile.OCR),
    SubTask("Recherche", PlanStepKind.ROUTE, ModelProfile.SYNTHESIS),
    SubTask("Raisonnement", PlanStepKind.ROUTE, ModelProfile.REASONING),
    SubTask("Rédaction", PlanStepKind.ROUTE, ModelProfile.DRAFTING),
    SubTask("Contrôle", PlanStepKind.CRITIQUE),
)


class TaskPlanner:
    """The sprint's "PLANNER": decomposes a complex task into
    sub-tasks, assigning each the best-suited model through
    `tmis.ai_fabric.router` — following the sprint's own example
    pipeline (Analyse documentaire→Vision, Extraction→OCR,
    Recherche→modèle spécialisé, Raisonnement→modèle logique,
    Rédaction→modèle rédactionnel, Contrôle→modèle critique). The
    final "Contrôle" stage deliberately never routes to a provider:
    it is executed by `tmis.ai_fabric.critic.CriticModel`, which "ne
    génère jamais, il évalue uniquement" — so it has no model to
    select."""

    def __init__(
        self, router: RouterEngine, pipeline: tuple[SubTask, ...] = DEFAULT_PIPELINE
    ) -> None:
        self._router = router
        self._pipeline = pipeline

    def plan(self, firm_id: str, task_description: str) -> ExecutionPlan:
        steps: list[PlannedStep] = []
        for sub_task in self._pipeline:
            if sub_task.kind is PlanStepKind.CRITIQUE:
                steps.append(PlannedStep(sub_task=sub_task))
                continue
            request = RoutingRequest(
                firm_id=firm_id,
                task_type=sub_task.name,
                prompt=task_description,
                profile=sub_task.profile,
            )
            decision = self._router.route(request)
            steps.append(PlannedStep(sub_task=sub_task, decision=decision))
        return ExecutionPlan(task_description=task_description, steps=tuple(steps))
