from tmis.workflow_automation.condition_engine.engine import ConditionEngine
from tmis.workflow_automation.simulation.schemas import SimulatedStepOutcome, SimulationReport
from tmis.workflow_automation.workflow_engine.schemas import Workflow


class SimulationEngine:
    """Dry-runs a workflow's conditions against a fictional context —
    read-only, never invokes `action_engine`, so it can never mutate
    real data regardless of what a step's action would otherwise do."""

    def __init__(self, condition_engine: ConditionEngine) -> None:
        self._condition_engine = condition_engine

    def simulate(self, workflow: Workflow, context: dict[str, str]) -> SimulationReport:
        for condition in workflow.conditions:
            if not self._condition_engine.evaluate(condition, context):
                return SimulationReport(
                    workflow_id=workflow.id,
                    would_complete=False,
                    workflow_condition_failure=(
                        "Une condition de niveau workflow n'est pas satisfaite par le "
                        "contexte fourni."
                    ),
                )

        outcomes: list[SimulatedStepOutcome] = []
        for step in sorted(workflow.steps, key=lambda s: s.order):
            if step.condition is None:
                outcomes.append(
                    SimulatedStepOutcome(step_order=step.order, name=step.name, would_run=True)
                )
                continue
            would_run = self._condition_engine.evaluate(step.condition, context)
            outcomes.append(
                SimulatedStepOutcome(
                    step_order=step.order,
                    name=step.name,
                    would_run=would_run,
                    skip_reason=None if would_run else "Condition de l'étape non satisfaite.",
                )
            )

        return SimulationReport(workflow_id=workflow.id, would_complete=True, steps=tuple(outcomes))
