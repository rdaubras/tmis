from tmis.strategic_intelligence.learning.ports import LearningStorePort
from tmis.strategic_intelligence.learning.schemas import (
    LearningRecord,
    StrategyOutcome,
    new_learning_record_id,
)


class LearningEngine:
    """Records what actually happened to a proposed strategy — chosen,
    validated, rejected, or modified — mirroring the acceptance-rate
    pattern of `cabinet_knowledge.feedback.FeedbackEngine`. This is the
    feedback loop the sprint's `recommendations/` submodule draws
    "similar past validated strategies" from."""

    def __init__(self, store: LearningStorePort) -> None:
        self._store = store

    def record_outcome(
        self,
        firm_id: str,
        case_id: str,
        strategy_id: str,
        strategy_type: str,
        outcome: StrategyOutcome,
        actor: str,
        comment: str = "",
    ) -> LearningRecord:
        record = LearningRecord(
            id=new_learning_record_id(),
            firm_id=firm_id,
            case_id=case_id,
            strategy_id=strategy_id,
            strategy_type=strategy_type,
            outcome=outcome,
            actor=actor,
            comment=comment,
        )
        self._store.save(record)
        return record

    def history_for_case(self, firm_id: str, case_id: str) -> list[LearningRecord]:
        return self._store.list_for_case(firm_id, case_id)

    def acceptance_rate_by_type(self, firm_id: str) -> dict[str, float]:
        records = self._store.list_for_firm(firm_id)
        by_type: dict[str, list[LearningRecord]] = {}
        for record in records:
            by_type.setdefault(record.strategy_type, []).append(record)

        rates: dict[str, float] = {}
        for strategy_type, type_records in by_type.items():
            accepted = sum(
                1
                for r in type_records
                if r.outcome in (StrategyOutcome.CHOSEN, StrategyOutcome.VALIDATED)
            )
            rates[strategy_type] = accepted / len(type_records)
        return rates
