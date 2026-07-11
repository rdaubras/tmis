from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain, TaxonomyNode


class InMemoryTaxonomyStore:
    def __init__(self) -> None:
        self._nodes: dict[str, TaxonomyNode] = {}

    def add(self, node: TaxonomyNode) -> None:
        self._nodes[node.id] = node

    def get(self, node_id: str) -> TaxonomyNode | None:
        return self._nodes.get(node_id)

    def list_by_domain(self, domain: LegalDomain) -> list[TaxonomyNode]:
        return [n for n in self._nodes.values() if n.domain is domain]

    def children_of(self, parent_id: str) -> list[TaxonomyNode]:
        return [n for n in self._nodes.values() if n.parent_id == parent_id]

    def list_all(self) -> list[TaxonomyNode]:
        return list(self._nodes.values())
