from tmis.ai_governance.provenance.ports import ProvenanceStorePort
from tmis.ai_governance.provenance.schemas import (
    ProvenanceGranularity,
    ProvenanceRecord,
    SourceType,
    new_provenance_record_id,
)


class ProvenanceEngine:
    """The sprint's "PROVENANCE ENGINE": records, for each element of
    a draft, the source it came from, at any of the four supported
    granularities — never a single flat citation list."""

    def __init__(self, store: ProvenanceStorePort) -> None:
        self._store = store

    def record(
        self,
        firm_id: str,
        production_id: str,
        *,
        granularity: ProvenanceGranularity,
        locator: str,
        excerpt: str,
        source_type: SourceType,
        source_reference: str,
        produced_by_agent: str | None = None,
        produced_by_model: str | None = None,
    ) -> ProvenanceRecord:
        record = ProvenanceRecord(
            id=new_provenance_record_id(),
            firm_id=firm_id,
            production_id=production_id,
            granularity=granularity,
            locator=locator,
            excerpt=excerpt,
            source_type=source_type,
            source_reference=source_reference,
            produced_by_agent=produced_by_agent,
            produced_by_model=produced_by_model,
        )
        self._store.add(record)
        return record

    def trace(self, firm_id: str, production_id: str) -> list[ProvenanceRecord]:
        return self._store.list_for_production(firm_id, production_id)

    def trace_at_granularity(
        self, firm_id: str, production_id: str, granularity: ProvenanceGranularity
    ) -> list[ProvenanceRecord]:
        return [r for r in self.trace(firm_id, production_id) if r.granularity is granularity]
