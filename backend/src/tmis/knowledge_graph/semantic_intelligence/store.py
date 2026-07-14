from tmis.knowledge_graph.semantic_intelligence.schemas import SemanticLink


class InMemorySemanticLinkStore:
    def __init__(self) -> None:
        self._links: list[SemanticLink] = []

    def save(self, link: SemanticLink) -> None:
        self._links.append(link)

    def list_for_object(self, object_id: str) -> list[SemanticLink]:
        return [
            link
            for link in self._links
            if link.source_id == object_id or link.target_id == object_id
        ]
