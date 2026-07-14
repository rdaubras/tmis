from tmis.knowledge_graph.entity_resolution.schemas import ResolvedEntity


class InMemoryResolvedEntityStore:
    def __init__(self) -> None:
        self._entities: dict[str, ResolvedEntity] = {}

    def save(self, entity: ResolvedEntity) -> None:
        self._entities[entity.id] = entity

    def get(self, firm_id: str, entity_id: str) -> ResolvedEntity | None:
        entity = self._entities.get(entity_id)
        if entity is None or entity.firm_id != firm_id:
            return None
        return entity

    def list_for_firm(self, firm_id: str) -> list[ResolvedEntity]:
        return [e for e in self._entities.values() if e.firm_id == firm_id]
