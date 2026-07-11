from typing import Protocol

from tmis.cabinet_knowledge.lineage.schemas import LineageRecord


class LineageStorePort(Protocol):
    def save(self, record: LineageRecord) -> None: ...

    def list_for_object(self, firm_id: str, knowledge_object_id: str) -> list[LineageRecord]: ...
