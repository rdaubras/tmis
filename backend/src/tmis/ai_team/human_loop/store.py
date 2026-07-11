from tmis.ai_team.human_loop.schemas import HumanDecision


class InMemoryHumanDecisionStore:
    def __init__(self) -> None:
        self._decisions: list[HumanDecision] = []

    def save(self, decision: HumanDecision) -> None:
        self._decisions.append(decision)

    def list_for_mission(self, mission_id: str) -> list[HumanDecision]:
        return [d for d in self._decisions if d.mission_id == mission_id]
