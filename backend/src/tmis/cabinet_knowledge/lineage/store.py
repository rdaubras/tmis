from tmis.cabinet_knowledge.lineage.schemas import LineageRecord


class InMemoryLineageStore:
    def __init__(self) -> None:
        self._records: list[LineageRecord] = []

    def save(self, record: LineageRecord) -> None:
        self._records.append(record)

    def list_for_object(self, firm_id: str, knowledge_object_id: str) -> list[LineageRecord]:
        return [
            r
            for r in self._records
            if r.firm_id == firm_id and r.knowledge_object_id == knowledge_object_id
        ]
