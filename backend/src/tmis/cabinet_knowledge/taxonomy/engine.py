from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.taxonomy.ports import TaxonomyStorePort
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain, TaxonomyNode

_TAG_PREFIX = "taxonomy:"


class TaxonomyEngine:
    """Classifies knowledge objects against a firm-independent tree of
    legal categories (default nodes are seeded once for the whole
    platform; a cabinet's own knowledge objects are what's tenant-
    scoped, not the taxonomy tree itself — every cabinet practices the
    same areas of law)."""

    def __init__(self, store: TaxonomyStorePort, knowledge_space: KnowledgeSpace) -> None:
        self._store = store
        self._knowledge_space = knowledge_space

    def classify(
        self, firm_id: str, object_id: str, node_ids: tuple[str, ...]
    ) -> frozenset[str]:
        for node_id in node_ids:
            if self._store.get(node_id) is None:
                raise KeyError(node_id)
        tags = frozenset(f"{_TAG_PREFIX}{node_id}" for node_id in node_ids)
        obj = self._knowledge_space.add_tags(firm_id, object_id, tags)
        return obj.tags

    def ancestors(self, node_id: str) -> list[TaxonomyNode]:
        chain: list[TaxonomyNode] = []
        current = self._store.get(node_id)
        while current is not None and current.parent_id is not None:
            parent = self._store.get(current.parent_id)
            if parent is None:
                break
            chain.append(parent)
            current = parent
        return chain

    def children(self, node_id: str) -> list[TaxonomyNode]:
        return self._store.children_of(node_id)

    def nodes_by_domain(self, domain: LegalDomain) -> list[TaxonomyNode]:
        return self._store.list_by_domain(domain)


def seed_default_taxonomy(store: TaxonomyStorePort) -> None:
    """Populates a small default classification tree — one root per
    `LegalDomain` plus a handful of representative subcategories, so
    the demo/tests have something realistic to classify against
    without requiring every cabinet to build its own tree from
    scratch."""
    if store.list_all():
        return
    roots = {
        domain: TaxonomyNode(id=f"taxo-root-{domain.value}", label=domain.value, domain=domain)
        for domain in LegalDomain
    }
    for root in roots.values():
        store.add(root)
    children = [
        TaxonomyNode(
            id="taxo-social-licenciement",
            label="Licenciement",
            domain=LegalDomain.SOCIAL,
            parent_id=roots[LegalDomain.SOCIAL].id,
        ),
        TaxonomyNode(
            id="taxo-social-contrat-travail",
            label="Contrat de travail",
            domain=LegalDomain.SOCIAL,
            parent_id=roots[LegalDomain.SOCIAL].id,
        ),
        TaxonomyNode(
            id="taxo-commercial-contentieux",
            label="Contentieux commercial",
            domain=LegalDomain.COMMERCIAL,
            parent_id=roots[LegalDomain.COMMERCIAL].id,
        ),
        TaxonomyNode(
            id="taxo-commercial-societes",
            label="Droit des sociétés",
            domain=LegalDomain.COMMERCIAL,
            parent_id=roots[LegalDomain.COMMERCIAL].id,
        ),
        TaxonomyNode(
            id="taxo-civil-recouvrement",
            label="Recouvrement de créances",
            domain=LegalDomain.CIVIL,
            parent_id=roots[LegalDomain.CIVIL].id,
        ),
    ]
    for node in children:
        store.add(node)
