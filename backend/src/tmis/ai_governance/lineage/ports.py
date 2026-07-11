from typing import Protocol

from tmis.ai_governance.lineage.schemas import LineageRecord


class LineageStorePort(Protocol):
    def add(self, record: LineageRecord) -> None: ...

    def list_for_production(self, firm_id: str, production_id: str) -> list[LineageRecord]: ...

    def get_latest(self, firm_id: str, production_id: str) -> LineageRecord | None: ...
