from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.cabinet_knowledge.approval.engine import ApprovalEngine
from tmis.cabinet_knowledge.approval.store import InMemoryApprovalStore
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.lineage.engine import LineageEngine
from tmis.cabinet_knowledge.lineage.store import InMemoryLineageStore
from tmis.cabinet_knowledge.ontology.schemas import RelationType
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.cabinet_knowledge.validation.schemas import ValidationDecision
from tmis.cabinet_knowledge.validation.store import InMemoryValidationStore
from tmis.document_intelligence.classification.keyword_classifier import KeywordClassifier
from tmis.document_intelligence.entities.regex_extractor import RegexEntityExtractor
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.graph_core.schemas import GraphNodeType
from tmis.legal_knowledge_graph.graph_core.store import (
    InMemoryGraphNodeStore,
    InMemoryGraphRelationStore,
)
from tmis.legal_knowledge_graph.ingestion.engine import KnowledgeIngestionPipeline
from tmis.legal_knowledge_graph.ingestion.schemas import IngestionSourceType
from tmis.legal_knowledge_graph.semantic_engine.engine import SemanticEngine

FIRM = "firm-a"
AUTHOR = "Julien Moreau"
APPROVER = "Camille Lefèvre"

_TEXT = (
    "Contrat de prestation conclu avec ACME Corp SARL, régi par l'article "
    "1134 du Code civil imposant la bonne foi contractuelle."
)


def _pipeline() -> tuple[KnowledgeIngestionPipeline, GraphEngine, KnowledgeSpace, ValidationEngine]:
    knowledge_space = KnowledgeSpace(InMemoryKnowledgeStore())
    governance = GovernanceEngine(InMemoryGovernanceStore(), knowledge_space)
    validation = ValidationEngine(InMemoryValidationStore(), knowledge_space, governance)
    approval = ApprovalEngine(InMemoryApprovalStore(), knowledge_space)
    lineage = LineageEngine(InMemoryLineageStore(), knowledge_space, governance)
    graph = GraphEngine(InMemoryGraphNodeStore(), InMemoryGraphRelationStore())
    semantic = SemanticEngine(HashingEmbeddingProvider(), KeywordClassifier())
    pipeline = KnowledgeIngestionPipeline(
        knowledge_space, lineage, validation, approval, RegexEntityExtractor(), semantic, graph
    )
    return pipeline, graph, knowledge_space, validation


async def test_ingest_creates_knowledge_object_and_graph_node() -> None:
    pipeline, graph, knowledge_space, _ = _pipeline()

    result = await pipeline.ingest(
        FIRM, IngestionSourceType.CONTRACT, "Contrat ACME", _TEXT, AUTHOR
    )

    obj = knowledge_space.get(FIRM, result.knowledge_object_id)
    assert obj is not None
    assert obj.status is KnowledgeStatus.IN_REVIEW

    node = graph.get_node(FIRM, result.graph_node_id)
    assert node.node_type is GraphNodeType.CONTRACT
    assert node.ref_id == result.knowledge_object_id


async def test_ingest_extracts_entities_and_links_them_as_concepts() -> None:
    pipeline, graph, _, _ = _pipeline()

    result = await pipeline.ingest(
        FIRM, IngestionSourceType.CONTRACT, "Contrat ACME", _TEXT, AUTHOR
    )

    assert "ACME Corp SARL" in result.extracted_entity_labels
    assert "article 1134" in result.extracted_entity_labels

    neighbor_labels = {n.label for n in graph.neighbors(FIRM, result.graph_node_id)}
    assert "ACME Corp SARL" in neighbor_labels
    relations = graph.relations_for(FIRM, result.graph_node_id)
    assert all(r.relation_type is RelationType.MENTIONS for r in relations)


async def test_ingest_classifies_content() -> None:
    pipeline, _, _, _ = _pipeline()

    result = await pipeline.ingest(
        FIRM, IngestionSourceType.CONTRACT, "Contrat ACME", _TEXT, AUTHOR
    )

    assert result.classification_category == "contract"


async def test_publish_requires_validation_to_have_approved_first() -> None:
    pipeline, _, knowledge_space, validation = _pipeline()

    result = await pipeline.ingest(
        FIRM, IngestionSourceType.CONTRACT, "Contrat ACME", _TEXT, AUTHOR
    )
    validation.decide(
        FIRM, result.validation_request_id, ValidationDecision.APPROVE, reviewer=APPROVER
    )

    published = pipeline.publish(FIRM, result.knowledge_object_id, APPROVER)

    assert published.status is KnowledgeStatus.VALIDATED
    assert published.is_published is True
    obj = knowledge_space.get(FIRM, result.knowledge_object_id)
    assert obj is not None
    assert obj.is_published is True
