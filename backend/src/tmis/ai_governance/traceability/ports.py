from typing import Protocol

from tmis.ai_governance.traceability.schemas import TraceEntry


class TraceStorePort(Protocol):
    def add(self, entry: TraceEntry) -> None: ...

    def list_for_production(self, firm_id: str, production_id: str) -> list[TraceEntry]: ...
