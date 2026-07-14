from typing import Protocol

from tmis.knowledge_graph.semantic_intelligence.schemas import SemanticLink


class SemanticLinkStorePort(Protocol):
    def save(self, link: SemanticLink) -> None: ...

    def list_for_object(self, object_id: str) -> list[SemanticLink]: ...
