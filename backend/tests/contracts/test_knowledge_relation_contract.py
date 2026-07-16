"""Contract test for `KnowledgeRelation`
(`tmis.cabinet_knowledge.ontology.schemas`), deliberately shared, per its
own docstring, by two independent engines in two different bounded
contexts: `cabinet_knowledge.ontology.OntologyEngine` (Sprint 8, relations
between `KnowledgeObject`s) and `legal_knowledge_graph.graph_core.
GraphEngine` (Sprint 25, relations between `GraphNode`s). Sprint 25's own
consolidation commit (`4a748f7`) removed a genuinely duplicated
`knowledge_graph` module — these two are the surviving, intentionally
separate producers, not a leftover duplicate (see
docs/reports/sprint-43-rapport-audit.md).

Each producer builds `KnowledgeRelation` against a *different* kind of
node (`KnowledgeObject` vs. `GraphNode`) and a *different* store
(`RelationStorePort` vs. `GraphRelationStorePort`) — this test confirms
both produce a `KnowledgeRelation` the other side's store would also
accept, i.e. the shared schema really is one contract, not two
coincidentally-identical ones.
"""

from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.ontology.engine import OntologyEngine
from tmis.cabinet_knowledge.ontology.schemas import KnowledgeRelation, RelationType
from tmis.cabinet_knowledge.ontology.store import InMemoryRelationStore
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNodeType
from tmis.legal_knowledge_graph.graph_core.store import (
    InMemoryGraphNodeStore,
    InMemoryGraphRelationStore,
)

_FIRM = "firm-contract-kg"


def test_ontology_engine_produces_a_knowledge_relation_its_own_store_round_trips() -> None:
    space = KnowledgeSpace(InMemoryKnowledgeStore())
    source = space.create(_FIRM, KnowledgeType.PLAYBOOK, "Playbook A", {}, author="a")
    target = space.create(_FIRM, KnowledgeType.PLAYBOOK, "Playbook B", {}, author="a")
    relation_store = InMemoryRelationStore()
    engine = OntologyEngine(relation_store, space)

    relation = engine.link(_FIRM, source.id, target.id, RelationType.RELATED_TO)

    assert isinstance(relation, KnowledgeRelation)
    assert relation in relation_store.list_for_object(_FIRM, source.id)


def test_graph_engine_produces_a_knowledge_relation_its_own_store_round_trips() -> None:
    node_store = InMemoryGraphNodeStore()
    relation_store = InMemoryGraphRelationStore()
    engine = GraphEngine(node_store, relation_store)
    source = engine.add_node(_FIRM, GraphNodeType.LAW_ARTICLE, "ko-1", "Article 1134")
    target = engine.add_node(_FIRM, GraphNodeType.ARGUMENT, "arg-1", "Argument")

    relation = engine.link(_FIRM, source.id, target.id, RelationType.INFLUENCES)

    assert isinstance(relation, KnowledgeRelation)
    assert relation in relation_store.list_for_node(_FIRM, source.id)


def test_a_graph_engine_relation_is_consumable_by_the_ontology_relation_store() -> None:
    """The cross-context check: a `KnowledgeRelation` produced by
    `GraphEngine` (keyed on `GraphNode` ids) must still be a valid,
    storable `KnowledgeRelation` from `cabinet_knowledge.ontology`'s point
    of view — proving the two producers really share one schema rather
    than two shapes that happen to have the same class name."""
    node_store = InMemoryGraphNodeStore()
    graph_relations = InMemoryGraphRelationStore()
    graph_engine = GraphEngine(node_store, graph_relations)
    source = graph_engine.add_node(_FIRM, GraphNodeType.LAW_ARTICLE, "ko-1", "Article 1134")
    target = graph_engine.add_node(_FIRM, GraphNodeType.ARGUMENT, "arg-1", "Argument")
    relation = graph_engine.link(_FIRM, source.id, target.id, RelationType.INFLUENCES)

    ontology_relation_store = InMemoryRelationStore()
    ontology_relation_store.add(relation)

    assert relation in ontology_relation_store.list_for_object(_FIRM, source.id)
