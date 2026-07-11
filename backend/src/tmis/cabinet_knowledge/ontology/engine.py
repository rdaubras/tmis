from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.ontology.ports import RelationStorePort
from tmis.cabinet_knowledge.ontology.schemas import (
    KnowledgeRelation,
    RelationType,
    new_relation_id,
)


class UnknownKnowledgeObjectError(KeyError):
    pass


class OntologyEngine:
    """Builds the knowledge graph between `KnowledgeObject`s — the
    relations `lineage/` and `recommendations/` read to explain
    provenance and similarity."""

    def __init__(self, store: RelationStorePort, knowledge_space: KnowledgeSpace) -> None:
        self._store = store
        self._knowledge_space = knowledge_space

    def link(
        self,
        firm_id: str,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
    ) -> KnowledgeRelation:
        for object_id in (source_id, target_id):
            if self._knowledge_space.get(firm_id, object_id) is None:
                raise UnknownKnowledgeObjectError(object_id)
        relation = KnowledgeRelation(
            id=new_relation_id(),
            firm_id=firm_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
        )
        self._store.add(relation)
        return relation

    def relations_for(self, firm_id: str, object_id: str) -> list[KnowledgeRelation]:
        return self._store.list_for_object(firm_id, object_id)
