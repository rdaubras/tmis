from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.ontology.engine import OntologyEngine
from tmis.cabinet_knowledge.ontology.store import InMemoryRelationStore
from tmis.case_intelligence.relationships.in_memory_graph import InMemoryCaseGraph
from tmis.case_intelligence.relationships.schemas import CaseNode, CaseNodeType
from tmis.document_intelligence.knowledge.in_memory_graph import InMemoryKnowledgeGraph
from tmis.knowledge_graph.copilot_bridge.engine import CopilotKnowledgeBridge
from tmis.knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.knowledge_graph.entity_resolution.schemas import EntityOccurrence
from tmis.knowledge_graph.entity_resolution.store import InMemoryResolvedEntityStore
from tmis.knowledge_graph.federation.engine import FederationQueryEngine
from tmis.knowledge_graph.federation.schemas import GraphOrigin
from tmis.legal_copilot_framework.knowledge_packs.engine import KnowledgePackEngine
from tmis.legal_copilot_framework.knowledge_packs.store import InMemoryKnowledgePackStore

FIRM = "firm-a"


_Fixture = tuple[
    CopilotKnowledgeBridge, KnowledgePackEngine, EntityResolutionEngine, InMemoryCaseGraph
]


def _bridge() -> _Fixture:
    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    pack_engine = KnowledgePackEngine(InMemoryKnowledgePackStore(), knowledge_space)
    resolution_engine = EntityResolutionEngine(
        InMemoryResolvedEntityStore(), HumanValidationEngine(InMemoryValidationStore())
    )
    case_graph = InMemoryCaseGraph()
    ontology = OntologyEngine(InMemoryRelationStore(), knowledge_space)
    federation = FederationQueryEngine(case_graph, InMemoryKnowledgeGraph(), ontology)
    bridge = CopilotKnowledgeBridge(pack_engine, resolution_engine, federation)
    return bridge, pack_engine, resolution_engine, case_graph


def test_attach_resolved_entities_only_keeps_valid_ids() -> None:
    bridge, pack_engine, resolution_engine, _ = _bridge()
    pack_engine.register_pack("kp-1", "Pack", LegalDomain.CIVIL)
    resolved = resolution_engine.resolve(
        FIRM,
        "user-1",
        [EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont")],
    )

    pack = bridge.attach_resolved_entities(FIRM, "kp-1", [resolved.id, "unknown-id"])

    assert pack.resolved_entity_ids == (resolved.id,)


def test_attach_resolved_entities_is_additive_across_versions() -> None:
    bridge, pack_engine, resolution_engine, _ = _bridge()
    pack_engine.register_pack("kp-1", "Pack", LegalDomain.CIVIL)
    first = resolution_engine.resolve(
        FIRM, "user-1", [EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="a", label="A")]
    )
    second = resolution_engine.resolve(
        FIRM, "user-1", [EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="b", label="B")]
    )

    bridge.attach_resolved_entities(FIRM, "kp-1", [first.id])
    pack = bridge.attach_resolved_entities(FIRM, "kp-1", [second.id])

    assert pack.version == 3
    assert set(pack.resolved_entity_ids) == {first.id, second.id}


def test_resolve_entities_returns_the_referenced_resolved_entities() -> None:
    bridge, pack_engine, resolution_engine, _ = _bridge()
    pack_engine.register_pack("kp-1", "Pack", LegalDomain.CIVIL)
    resolved = resolution_engine.resolve(
        FIRM, "user-1", [EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="a", label="A")]
    )
    bridge.attach_resolved_entities(FIRM, "kp-1", [resolved.id])

    assert [e.id for e in bridge.resolve_entities(FIRM, "kp-1")] == [resolved.id]


def test_attach_and_resolve_federated_relations() -> None:
    bridge, pack_engine, _, case_graph = _bridge()
    case_graph.add_node(CaseNode(id="actor-1", type=CaseNodeType.ACTOR, label="Jean Dupont"))
    pack_engine.register_pack("kp-1", "Pack", LegalDomain.CIVIL)

    bridge.attach_federated_relations(FIRM, "kp-1", [(GraphOrigin.CASE_GRAPH, "actor-1")])
    neighborhoods = bridge.resolve_federated_relations(FIRM, "kp-1")

    assert len(neighborhoods) == 1
    assert neighborhoods[0].subject.node_id == "actor-1"


def test_resolve_federated_relations_with_no_refs_is_empty() -> None:
    bridge, pack_engine, _, _ = _bridge()
    pack_engine.register_pack("kp-1", "Pack", LegalDomain.CIVIL)

    assert bridge.resolve_federated_relations(FIRM, "kp-1") == ()
