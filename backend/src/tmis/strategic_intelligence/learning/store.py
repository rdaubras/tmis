from tmis.strategic_intelligence.learning.schemas import LearningRecord


class InMemoryLearningStore:
    def __init__(self) -> None:
        self._records: list[LearningRecord] = []

    def save(self, record: LearningRecord) -> None:
        self._records.append(record)

    def list_for_case(self, firm_id: str, case_id: str) -> list[LearningRecord]:
        return [r for r in self._records if r.firm_id == firm_id and r.case_id == case_id]

    def list_for_firm(self, firm_id: str) -> list[LearningRecord]:
        return [r for r in self._records if r.firm_id == firm_id]
