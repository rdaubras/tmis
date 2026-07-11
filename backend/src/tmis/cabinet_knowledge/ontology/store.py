from tmis.cabinet_knowledge.ontology.schemas import KnowledgeRelation


class InMemoryRelationStore:
    def __init__(self) -> None:
        self._relations: list[KnowledgeRelation] = []

    def add(self, relation: KnowledgeRelation) -> None:
        self._relations.append(relation)

    def list_for_object(self, firm_id: str, object_id: str) -> list[KnowledgeRelation]:
        return [
            r
            for r in self._relations
            if r.firm_id == firm_id and (r.source_id == object_id or r.target_id == object_id)
        ]
