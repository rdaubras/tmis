from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeObject, KnowledgeType


class InMemoryKnowledgeStore:
    def __init__(self) -> None:
        self._objects: dict[str, KnowledgeObject] = {}

    def save(self, obj: KnowledgeObject) -> None:
        self._objects[obj.id] = obj

    def get(self, object_id: str) -> KnowledgeObject | None:
        return self._objects.get(object_id)

    def list_for_firm(
        self, firm_id: str, type_: KnowledgeType | None = None
    ) -> list[KnowledgeObject]:
        return [
            obj
            for obj in self._objects.values()
            if obj.firm_id == firm_id and (type_ is None or obj.type is type_)
        ]
