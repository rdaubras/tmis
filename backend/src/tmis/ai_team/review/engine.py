from tmis.ai.schemas.agent import AgentOutput
from tmis.ai_team.critique.engine import CritiqueEngine
from tmis.ai_team.review.schemas import ReviewDecision, ReviewRecord


class ReviewEngine:
    """Turns a `Critique` into one of three review decisions (see
    docs/57-guide-critique.md — Review): `APPROVED` when the critique
    is clean, `REJECTED` when the production looks substantively
    incomplete, `REVISION_REQUESTED` for every other non-empty
    critique. This decision is advisory — `tmis.ai_team.human_loop`
    always has the final say, per the sprint's human-validation
    constraint."""

    def __init__(self, critique_engine: CritiqueEngine) -> None:
        self._critique_engine = critique_engine

    def review(
        self, mission_id: str, sub_task_id: str, agent_id: str, output: AgentOutput
    ) -> ReviewRecord:
        critique = self._critique_engine.critique(sub_task_id, agent_id, output)
        if critique.is_clean:
            decision = ReviewDecision.APPROVED
        elif any("incomplète" in issue for issue in critique.issues):
            decision = ReviewDecision.REJECTED
        else:
            decision = ReviewDecision.REVISION_REQUESTED

        return ReviewRecord(
            mission_id=mission_id, sub_task_id=sub_task_id, critique=critique, decision=decision
        )
