from typing import Protocol

from tmis.legal_reasoning.planner.schemas import ReasoningPlan


class ReasoningPlannerPort(Protocol):
    """Port implemented by every interchangeable reasoning planner."""

    def build_plan(self, question: str, case_id: str | None) -> ReasoningPlan: ...
