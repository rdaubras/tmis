from typing import Protocol

from tmis.knowledge_graph.entity_resolution.schemas import ResolvedEntity


class ResolvedEntityStorePort(Protocol):
    def save(self, entity: ResolvedEntity) -> None: ...

    def get(self, firm_id: str, entity_id: str) -> ResolvedEntity | None: ...

    def list_for_firm(self, firm_id: str) -> list[ResolvedEntity]: ...
