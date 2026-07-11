from typing import Protocol

from tmis.ai_team.human_loop.schemas import HumanDecision


class HumanDecisionStorePort(Protocol):
    def save(self, decision: HumanDecision) -> None: ...

    def list_for_mission(self, mission_id: str) -> list[HumanDecision]: ...
