from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import (
    ValidationDecisionType,
    ValidationRequest,
)


class StrategyReviewAdapter:
    """Thin adapter reusing
    `ai_governance.human_validation.HumanValidationEngine` directly for
    strategy review — avoids a third reimplementation of the
    approval-workflow pattern (after `cabinet_knowledge.validation` and
    `collaboration.approvals`). A strategy's `id` is passed as the
    engine's `production_id`, so every review is automatically visible
    through the AI Governance Platform's own audit trail."""

    def __init__(self, human_validation_engine: HumanValidationEngine) -> None:
        self._human_validation = human_validation_engine

    def request_review(
        self,
        firm_id: str,
        strategy_id: str,
        requested_by: str,
        approver_ids: tuple[str, ...],
    ) -> ValidationRequest:
        return self._human_validation.request_simple(
            firm_id, strategy_id, requested_by, approver_ids
        )

    def decide(
        self,
        firm_id: str,
        request_id: str,
        approver_id: str,
        decision: ValidationDecisionType,
        comment: str | None = None,
    ) -> ValidationRequest:
        return self._human_validation.decide(firm_id, request_id, approver_id, decision, comment)

    def history(self, firm_id: str, strategy_id: str) -> list[ValidationRequest]:
        return self._human_validation.history(firm_id, strategy_id)

    def is_validated(self, firm_id: str, strategy_id: str) -> bool:
        return self._human_validation.is_validated(firm_id, strategy_id)
