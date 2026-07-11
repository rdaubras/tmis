from typing import Protocol

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType


class KnowledgeStorePort(Protocol):
    def save(self, obj: KnowledgeObject) -> None: ...

    def get(self, object_id: str) -> KnowledgeObject | None: ...

    def list_for_firm(
        self, firm_id: str, type_: KnowledgeType | None = None
    ) -> list[KnowledgeObject]: ...
