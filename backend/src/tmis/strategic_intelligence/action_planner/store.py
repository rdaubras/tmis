from tmis.strategic_intelligence.action_planner.schemas import ActionStep


class InMemoryActionPlanStore:
    def __init__(self) -> None:
        self._steps: dict[tuple[str, str], ActionStep] = {}

    def add(self, firm_id: str, step: ActionStep) -> None:
        self._steps[(firm_id, step.id)] = step

    def get(self, firm_id: str, step_id: str) -> ActionStep | None:
        return self._steps.get((firm_id, step_id))

    def remove(self, firm_id: str, step_id: str) -> None:
        self._steps.pop((firm_id, step_id), None)

    def list_for_strategy(self, firm_id: str, strategy_id: str) -> list[ActionStep]:
        steps = [
            s
            for (fid, _), s in self._steps.items()
            if fid == firm_id and s.strategy_id == strategy_id
        ]
        return sorted(steps, key=lambda s: s.order)
