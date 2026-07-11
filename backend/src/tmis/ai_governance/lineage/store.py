from tmis.ai_governance.lineage.schemas import LineageRecord


class InMemoryLineageStore:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], list[LineageRecord]] = {}

    def add(self, record: LineageRecord) -> None:
        self._records.setdefault((record.firm_id, record.production_id), []).append(record)

    def list_for_production(self, firm_id: str, production_id: str) -> list[LineageRecord]:
        return list(self._records.get((firm_id, production_id), []))

    def get_latest(self, firm_id: str, production_id: str) -> LineageRecord | None:
        records = self._records.get((firm_id, production_id), [])
        return records[-1] if records else None
