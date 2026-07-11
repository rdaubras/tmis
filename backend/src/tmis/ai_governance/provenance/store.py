from tmis.ai_governance.provenance.schemas import ProvenanceRecord


class InMemoryProvenanceStore:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str], list[ProvenanceRecord]] = {}

    def add(self, record: ProvenanceRecord) -> None:
        self._records.setdefault((record.firm_id, record.production_id), []).append(record)

    def list_for_production(self, firm_id: str, production_id: str) -> list[ProvenanceRecord]:
        return list(self._records.get((firm_id, production_id), []))
