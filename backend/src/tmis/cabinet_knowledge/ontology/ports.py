from typing import Protocol

from tmis.cabinet_knowledge.ontology.schemas import KnowledgeRelation


class RelationStorePort(Protocol):
    def add(self, relation: KnowledgeRelation) -> None: ...

    def list_for_object(self, firm_id: str, object_id: str) -> list[KnowledgeRelation]: ...
