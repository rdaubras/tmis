from tmis.ai_governance.decision_records.ports import DecisionRecordStorePort
from tmis.ai_governance.decision_records.schemas import DecisionRecord, new_decision_record_id


class DecisionRecordEngine:
    """The sprint's "DECISION RECORDS" registry — every meaningful
    decision an AI production takes is captured once and never
    rewritten; `history()` is the append-only audit trail a lawyer can
    replay."""

    def __init__(self, store: DecisionRecordStorePort) -> None:
        self._store = store

    def record(
        self,
        firm_id: str,
        production_id: str,
        *,
        context: str,
        objective: str,
        hypotheses_considered: tuple[str, ...] = (),
        alternatives_considered: tuple[str, ...] = (),
        decision: str,
        justification: str,
        impacts: tuple[str, ...] = (),
    ) -> DecisionRecord:
        record = DecisionRecord(
            id=new_decision_record_id(),
            firm_id=firm_id,
            production_id=production_id,
            context=context,
            objective=objective,
            hypotheses_considered=hypotheses_considered,
            alternatives_considered=alternatives_considered,
            decision=decision,
            justification=justification,
            impacts=impacts,
        )
        self._store.add(record)
        return record

    def history(self, firm_id: str, production_id: str) -> list[DecisionRecord]:
        return self._store.list_for_production(firm_id, production_id)
