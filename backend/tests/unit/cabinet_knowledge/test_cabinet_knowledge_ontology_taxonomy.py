import pytest

from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.ontology.engine import OntologyEngine, UnknownKnowledgeObjectError
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.cabinet_knowledge.ontology.store import InMemoryRelationStore
from tmis.cabinet_knowledge.taxonomy.engine import TaxonomyEngine, seed_default_taxonomy
from tmis.cabinet_knowledge.taxonomy.schemas import LegalDomain
from tmis.cabinet_knowledge.taxonomy.store import InMemoryTaxonomyStore

FIRM = "firm-a"


def _space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


def test_ontology_link_between_two_existing_objects() -> None:
    space = _space()
    a = space.create(FIRM, KnowledgeType.NOTE, "A", {}, "avocat1")
    b = space.create(FIRM, KnowledgeType.NOTE, "B", {}, "avocat1")
    engine = OntologyEngine(InMemoryRelationStore(), space)

    relation = engine.link(FIRM, a.id, b.id, RelationType.CITES)

    assert relation.source_id == a.id
    assert engine.relations_for(FIRM, a.id) == [relation]
    assert engine.relations_for(FIRM, b.id) == [relation]


def test_ontology_link_rejects_unknown_object() -> None:
    space = _space()
    a = space.create(FIRM, KnowledgeType.NOTE, "A", {}, "avocat1")
    engine = OntologyEngine(InMemoryRelationStore(), space)

    with pytest.raises(UnknownKnowledgeObjectError):
        engine.link(FIRM, a.id, "unknown", RelationType.CITES)


def test_taxonomy_seed_is_idempotent() -> None:
    store = InMemoryTaxonomyStore()
    seed_default_taxonomy(store)
    count_after_first_seed = len(store.list_all())

    seed_default_taxonomy(store)

    assert len(store.list_all()) == count_after_first_seed
    social_nodes = [n for n in store.list_all() if n.domain is LegalDomain.SOCIAL]
    assert len(social_nodes) >= 1


def test_taxonomy_classify_tags_object() -> None:
    space = _space()
    store = InMemoryTaxonomyStore()
    seed_default_taxonomy(store)
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    engine = TaxonomyEngine(store, space)

    tags = engine.classify(FIRM, obj.id, ("taxo-social-licenciement",))

    assert "taxonomy:taxo-social-licenciement" in tags


def test_taxonomy_classify_rejects_unknown_node() -> None:
    space = _space()
    store = InMemoryTaxonomyStore()
    seed_default_taxonomy(store)
    obj = space.create(FIRM, KnowledgeType.NOTE, "N", {}, "avocat1")
    engine = TaxonomyEngine(store, space)

    with pytest.raises(KeyError):
        engine.classify(FIRM, obj.id, ("unknown-node",))


def test_taxonomy_ancestors_and_children() -> None:
    store = InMemoryTaxonomyStore()
    seed_default_taxonomy(store)
    engine = TaxonomyEngine(store, _space())

    ancestors = engine.ancestors("taxo-social-licenciement")
    assert ancestors[0].id == "taxo-root-social"

    children = engine.children("taxo-root-social")
    assert {c.id for c in children} == {"taxo-social-licenciement", "taxo-social-contrat-travail"}
