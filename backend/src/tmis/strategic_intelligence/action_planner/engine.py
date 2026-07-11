from tmis.strategic_intelligence.action_planner.ports import ActionPlanStorePort
from tmis.strategic_intelligence.action_planner.schemas import ActionStep, new_action_step_id


class ActionPlannerEngine:
    """Builds and edits a strategy's action plan. Every mutation is
    immediate and unrestricted — no state machine, no approval gate —
    because the plan belongs entirely to the avocat once proposed."""

    def __init__(self, store: ActionPlanStorePort) -> None:
        self._store = store

    def add_step(
        self,
        firm_id: str,
        strategy_id: str,
        description: str,
        category: str,
        order: int | None = None,
    ) -> ActionStep:
        if order is None:
            order = len(self._store.list_for_strategy(firm_id, strategy_id))
        step = ActionStep(
            id=new_action_step_id(),
            strategy_id=strategy_id,
            description=description,
            category=category,
            order=order,
        )
        self._store.add(firm_id, step)
        return step

    def remove_step(self, firm_id: str, step_id: str) -> None:
        self._store.remove(firm_id, step_id)

    def mark_done(self, firm_id: str, step_id: str, done: bool = True) -> ActionStep:
        step = self._store.get(firm_id, step_id)
        if step is None:
            raise KeyError(step_id)
        step.done = done
        return step

    def reorder(self, firm_id: str, strategy_id: str, ordered_step_ids: tuple[str, ...]) -> None:
        for new_order, step_id in enumerate(ordered_step_ids):
            step = self._store.get(firm_id, step_id)
            if step is None or step.strategy_id != strategy_id:
                raise KeyError(step_id)
            step.order = new_order

    def list_for_strategy(self, firm_id: str, strategy_id: str) -> list[ActionStep]:
        return self._store.list_for_strategy(firm_id, strategy_id)
