"""Integration test: resolving one real-world entity across the three
real graphs, then using `FederationQueryEngine` to gather what is
connected to it in each scope — the end-to-end "tout ce qui touche
l'entité X, dans quel dossier, quel document, quelle recommandation
cabinet" query the sprint describes, plus the human-validation path
for a low-confidence resolution."""

from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.ontology.engine import OntologyEngine
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.cabinet_knowledge.ontology.store import InMemoryRelationStore
from tmis.case_intelligence.relationships.in_memory_graph import InMemoryCaseGraph
from tmis.case_intelligence.relationships.schemas import CaseEdge, CaseNode, CaseNodeType
from tmis.document_intelligence.knowledge.in_memory_graph import InMemoryKnowledgeGraph
from tmis.document_intelligence.schemas.knowledge import KnowledgeEdge, KnowledgeNode, NodeType
from tmis.knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.knowledge_graph.entity_resolution.schemas import EntityOccurrence, ResolutionStatus
from tmis.knowledge_graph.entity_resolution.store import InMemoryResolvedEntityStore
from tmis.knowledge_graph.federation.engine import FederationQueryEngine
from tmis.knowledge_graph.federation.schemas import GraphOrigin

FIRM = "firm-a"


def test_resolved_entity_drives_a_real_cross_scope_federation_query() -> None:
    case_graph = InMemoryCaseGraph()
    case_graph.add_node(CaseNode(id="actor-1", type=CaseNodeType.ACTOR, label="Jean Dupont"))
    case_graph.add_node(CaseNode(id="doc-ref-1", type=CaseNodeType.DOCUMENT, label="bail.txt"))
    case_graph.add_edge(
        CaseEdge(source_id="actor-1", target_id="doc-ref-1", relation="mentioned_in")
    )

    document_graph = InMemoryKnowledgeGraph()
    document_graph.add_node(
        KnowledgeNode(id="entity-1", type=NodeType.ENTITY, label="Jean Dupont")
    )
    document_graph.add_node(KnowledgeNode(id="doc-1", type=NodeType.DOCUMENT, label="bail.txt"))
    document_graph.add_edge(
        KnowledgeEdge(source_id="doc-1", target_id="entity-1", relation="mentions")
    )

    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    ontology = OntologyEngine(InMemoryRelationStore(), knowledge_space)
    recommendation = knowledge_space.create(
        FIRM, KnowledgeType.PLAYBOOK, "Playbook Jean Dupont", {}, "author"
    )
    related = knowledge_space.create(FIRM, KnowledgeType.CLAUSE, "Clause associée", {}, "author")
    ontology.link(FIRM, recommendation.id, related.id, RelationType.RELATED_TO)

    resolution_engine = EntityResolutionEngine(
        InMemoryResolvedEntityStore(), HumanValidationEngine(InMemoryValidationStore())
    )
    resolved = resolution_engine.resolve(
        FIRM,
        "user-1",
        [
            EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="Jean Dupont"),
            EntityOccurrence(
                origin=GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH, node_id="entity-1", label="Jean Dupont"
            ),
        ],
    )
    assert resolved.status is ResolutionStatus.CONFIRMED

    federation = FederationQueryEngine(case_graph, document_graph, ontology)
    occurrences = [(o.origin, o.node_id) for o in resolved.occurrences]
    occurrences.append((GraphOrigin.CABINET_ONTOLOGY, recommendation.id))

    neighborhoods = federation.cross_scope_neighborhood(FIRM, occurrences)

    assert len(neighborhoods) == 3
    origins = {n.subject.origin for n in neighborhoods}
    assert origins == {
        GraphOrigin.CASE_GRAPH,
        GraphOrigin.DOCUMENT_KNOWLEDGE_GRAPH,
        GraphOrigin.CABINET_ONTOLOGY,
    }
    cabinet_result = next(
        n for n in neighborhoods if n.subject.origin is GraphOrigin.CABINET_ONTOLOGY
    )
    assert [n.node_id for n in cabinet_result.neighbors] == [related.id]


def test_low_confidence_resolution_is_confirmed_only_after_human_approval() -> None:
    validation_store = InMemoryValidationStore()
    human_validation = HumanValidationEngine(validation_store)
    resolution_engine = EntityResolutionEngine(InMemoryResolvedEntityStore(), human_validation)

    resolved = resolution_engine.resolve(
        FIRM,
        "user-1",
        [
            EntityOccurrence(origin=GraphOrigin.CASE_GRAPH, node_id="actor-1", label="J. Dupont"),
            EntityOccurrence(
                origin=GraphOrigin.CABINET_ONTOLOGY, node_id="know-1", label="ACME Corp"
            ),
        ],
        approver_ids=("partner-1",),
    )
    assert resolved.status is ResolutionStatus.PENDING_VALIDATION

    pending_requests = human_validation.history(FIRM, resolved.id)
    assert len(pending_requests) == 1
    assert pending_requests[0].id == resolved.validation_request_id

    confirmed = resolution_engine.decide(
        FIRM, resolved.id, "partner-1", ValidationDecisionType.APPROVE
    )

    assert confirmed.status is ResolutionStatus.CONFIRMED
    assert human_validation.is_validated(FIRM, resolved.id) is True
