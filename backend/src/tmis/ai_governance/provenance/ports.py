from typing import Protocol

from tmis.ai_governance.provenance.schemas import ProvenanceRecord


class ProvenanceStorePort(Protocol):
    def add(self, record: ProvenanceRecord) -> None: ...

    def list_for_production(self, firm_id: str, production_id: str) -> list[ProvenanceRecord]: ...
