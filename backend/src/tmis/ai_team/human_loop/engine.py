from tmis.ai_team.human_loop.ports import HumanDecisionStorePort
from tmis.ai_team.human_loop.schemas import HumanDecision, HumanDecisionType, new_decision_id


class HumanLoopEngine:
    """Captures every human decision on a mission and its full history
    (see docs/55-guide-coordinateur.md — Human in the Loop). This
    engine only records *intent* — it never mutates a `Mission` or
    `Team` itself; `CoordinatorEngine.apply_human_decision` is what
    turns a recorded decision into an actual effect (excluding an
    agent, re-enqueuing steps...), keeping the audit trail independent
    of whether — or how — a decision was ultimately acted upon."""

    def __init__(self, store: HumanDecisionStorePort) -> None:
        self._store = store

    def _record(
        self, mission_id: str, actor_id: str, decision_type: HumanDecisionType, **payload: str
    ) -> HumanDecision:
        decision = HumanDecision(
            id=new_decision_id(),
            mission_id=mission_id,
            actor_id=actor_id,
            decision_type=decision_type,
            payload=payload,
        )
        self._store.save(decision)
        return decision

    def approve(self, mission_id: str, actor_id: str) -> HumanDecision:
        return self._record(mission_id, actor_id, HumanDecisionType.APPROVE)

    def request_new_analysis(
        self, mission_id: str, actor_id: str, sub_task_id: str
    ) -> HumanDecision:
        return self._record(
            mission_id, actor_id, HumanDecisionType.REQUEST_NEW_ANALYSIS, sub_task_id=sub_task_id
        )

    def exclude_agent(self, mission_id: str, actor_id: str, agent_id: str) -> HumanDecision:
        return self._record(
            mission_id, actor_id, HumanDecisionType.EXCLUDE_AGENT, agent_id=agent_id
        )

    def add_agent(self, mission_id: str, actor_id: str, agent_id: str) -> HumanDecision:
        return self._record(mission_id, actor_id, HumanDecisionType.ADD_AGENT, agent_id=agent_id)

    def modify_plan(self, mission_id: str, actor_id: str, note: str) -> HumanDecision:
        return self._record(mission_id, actor_id, HumanDecisionType.MODIFY_PLAN, note=note)

    def rerun_steps(self, mission_id: str, actor_id: str, sub_task_ids: list[str]) -> HumanDecision:
        return self._record(
            mission_id, actor_id, HumanDecisionType.RERUN_STEPS, sub_task_ids=",".join(sub_task_ids)
        )

    def history_for_mission(self, mission_id: str) -> list[HumanDecision]:
        return self._store.list_for_mission(mission_id)
