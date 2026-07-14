from functools import lru_cache

from tmis.ai.embeddings.hashing_provider import HashingEmbeddingProvider
from tmis.ai.embeddings.ports import EmbeddingProviderPort
from tmis.ai_governance.bootstrap import get_human_validation_engine
from tmis.cabinet_knowledge.bootstrap import (
    get_approval_engine,
    get_knowledge_space,
    get_lineage_engine,
    get_quality_engine,
    get_validation_engine,
)
from tmis.cloud_operations.bootstrap import get_metrics_engine
from tmis.document_intelligence.classification.keyword_classifier import KeywordClassifier
from tmis.document_intelligence.classification.ports import ClassifierPort
from tmis.document_intelligence.entities.ports import EntityExtractorPort
from tmis.document_intelligence.entities.regex_extractor import RegexEntityExtractor
from tmis.legal_copilot_framework.bootstrap import get_context_engine
from tmis.legal_knowledge_graph.analytics.engine import GraphAnalyticsEngine
from tmis.legal_knowledge_graph.copilot_bridge.engine import KnowledgeGraphQueryEngine
from tmis.legal_knowledge_graph.demo.deps import LkgDemoDeps
from tmis.legal_knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.legal_knowledge_graph.entity_resolution.store import InMemoryResolutionMatchStore
from tmis.legal_knowledge_graph.governance.engine import GraphAccessPolicyEngine
from tmis.legal_knowledge_graph.governance.store import InMemoryNodeAccessPolicyStore
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.graph_core.store import (
    InMemoryGraphNodeStore,
    InMemoryGraphRelationStore,
)
from tmis.legal_knowledge_graph.human_validation.engine import GraphFeedbackEngine
from tmis.legal_knowledge_graph.human_validation.store import InMemoryGraphFeedbackStore
from tmis.legal_knowledge_graph.ingestion.engine import KnowledgeIngestionPipeline
from tmis.legal_knowledge_graph.quality.engine import GraphQualityEngine
from tmis.legal_knowledge_graph.semantic_engine.engine import SemanticEngine


@lru_cache
def get_embedding_provider() -> EmbeddingProviderPort:
    """The same deterministic, dependency-free embedding every other
    part of TMIS uses (`ai.kernel`, `ai.rag`, `document_intelligence.
    embeddings`) — never a second embedding model."""
    return HashingEmbeddingProvider()


@lru_cache
def get_entity_extractor() -> EntityExtractorPort:
    return RegexEntityExtractor()


@lru_cache
def get_classifier() -> ClassifierPort:
    return KeywordClassifier()


@lru_cache
def get_graph_engine() -> GraphEngine:
    return GraphEngine(InMemoryGraphNodeStore(), InMemoryGraphRelationStore())


@lru_cache
def get_semantic_engine() -> SemanticEngine:
    return SemanticEngine(get_embedding_provider(), get_classifier())


@lru_cache
def get_entity_resolution_engine() -> EntityResolutionEngine:
    return EntityResolutionEngine(
        InMemoryResolutionMatchStore(),
        get_graph_engine(),
        get_embedding_provider(),
        get_human_validation_engine(),
    )


@lru_cache
def get_ingestion_pipeline() -> KnowledgeIngestionPipeline:
    return KnowledgeIngestionPipeline(
        get_knowledge_space(),
        get_lineage_engine(),
        get_validation_engine(),
        get_approval_engine(),
        get_entity_extractor(),
        get_semantic_engine(),
        get_graph_engine(),
    )


@lru_cache
def get_graph_feedback_engine() -> GraphFeedbackEngine:
    return GraphFeedbackEngine(InMemoryGraphFeedbackStore())


@lru_cache
def get_knowledge_graph_query_engine() -> KnowledgeGraphQueryEngine:
    return KnowledgeGraphQueryEngine(
        get_graph_engine(), get_semantic_engine(), get_knowledge_space()
    )


@lru_cache
def get_graph_access_policy_engine() -> GraphAccessPolicyEngine:
    return GraphAccessPolicyEngine(InMemoryNodeAccessPolicyStore())


@lru_cache
def get_graph_quality_engine() -> GraphQualityEngine:
    return GraphQualityEngine(
        get_quality_engine(), get_lineage_engine(), get_graph_engine(), get_knowledge_space()
    )


@lru_cache
def get_graph_analytics_engine() -> GraphAnalyticsEngine:
    return GraphAnalyticsEngine(get_metrics_engine())


def get_lkg_demo_deps() -> LkgDemoDeps:
    """Bundles every engine the Phase 11 demo scenario needs, reusing
    the same process-wide singletons every other getter in this module
    already returns."""
    return LkgDemoDeps(
        graph=get_graph_engine(),
        semantic=get_semantic_engine(),
        ingestion=get_ingestion_pipeline(),
        validation=get_validation_engine(),
        approval=get_approval_engine(),
        entity_resolution=get_entity_resolution_engine(),
        feedback=get_graph_feedback_engine(),
        governance=get_graph_access_policy_engine(),
        quality=get_graph_quality_engine(),
        analytics=get_graph_analytics_engine(),
        copilot_query=get_knowledge_graph_query_engine(),
        context_engine=get_context_engine(),
    )
