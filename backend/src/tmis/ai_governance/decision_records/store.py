from tmis.ai_governance.decision_records.schemas import DecisionRecord


class InMemoryDecisionRecordStore:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], list[DecisionRecord]] = {}

    def add(self, record: DecisionRecord) -> None:
        self._records.setdefault((record.firm_id, record.production_id), []).append(record)

    def list_for_production(self, firm_id: str, production_id: str) -> list[DecisionRecord]:
        return list(self._records.get((firm_id, production_id), []))
