"""Process-wide composition root for `tmis.knowledge_graph` (see
docs/145-architecture-knowledge-graph.md) — every dependency below is
composed from an existing bounded context's engine, never a new
storage mechanism, matching the "aucun quatrième moteur de graphe"
constraint of Sprint 25.
"""

from functools import lru_cache

from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.store import InMemoryGovernancePolicyStore
from tmis.cabinet_knowledge.governance.engine import GovernanceEngine
from tmis.cabinet_knowledge.governance.store import InMemoryGovernanceStore
from tmis.cabinet_knowledge.knowledge.engine import KnowledgeSpace
from tmis.cabinet_knowledge.knowledge.store import InMemoryKnowledgeStore
from tmis.cabinet_knowledge.ontology.engine import OntologyEngine
from tmis.cabinet_knowledge.ontology.store import InMemoryRelationStore
from tmis.case_intelligence.relationships.in_memory_graph import InMemoryCaseGraph
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.document_intelligence.knowledge.in_memory_graph import InMemoryKnowledgeGraph
from tmis.knowledge_graph.analytics.engine import KnowledgeGraphAnalytics
from tmis.knowledge_graph.copilot_bridge.engine import CopilotKnowledgeBridge
from tmis.knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.knowledge_graph.entity_resolution.store import InMemoryResolvedEntityStore
from tmis.knowledge_graph.federation.engine import FederationQueryEngine
from tmis.knowledge_graph.governance.engine import KnowledgeGraphGovernance
from tmis.knowledge_graph.semantic_intelligence.engine import SemanticLinkEngine
from tmis.knowledge_graph.semantic_intelligence.store import InMemorySemanticLinkStore
from tmis.legal_copilot_framework.knowledge_packs.engine import KnowledgePackEngine
from tmis.legal_copilot_framework.knowledge_packs.store import InMemoryKnowledgePackStore
from tmis.platform.metrics.bootstrap import get_metrics_registry


@lru_cache
def get_case_graph() -> InMemoryCaseGraph:
    return InMemoryCaseGraph()


@lru_cache
def get_document_knowledge_graph() -> InMemoryKnowledgeGraph:
    return InMemoryKnowledgeGraph()


@lru_cache
def get_cabinet_knowledge_space() -> KnowledgeSpace:
    return KnowledgeSpace(InMemoryKnowledgeStore())


@lru_cache
def get_ontology_engine() -> OntologyEngine:
    return OntologyEngine(InMemoryRelationStore(), get_cabinet_knowledge_space())


@lru_cache
def get_cabinet_governance_engine() -> GovernanceEngine:
    return GovernanceEngine(InMemoryGovernanceStore(), get_cabinet_knowledge_space())


@lru_cache
def get_federation_query_engine() -> FederationQueryEngine:
    return FederationQueryEngine(
        get_case_graph(), get_document_knowledge_graph(), get_ontology_engine()
    )


@lru_cache
def get_human_validation_engine() -> HumanValidationEngine:
    return HumanValidationEngine(InMemoryValidationStore())


@lru_cache
def get_entity_resolution_engine() -> EntityResolutionEngine:
    return EntityResolutionEngine(InMemoryResolvedEntityStore(), get_human_validation_engine())


@lru_cache
def get_semantic_link_engine() -> SemanticLinkEngine:
    return SemanticLinkEngine(InMemorySemanticLinkStore())


@lru_cache
def get_knowledge_graph_metrics_engine() -> MetricsEngine:
    return MetricsEngine(InMemoryMetricEventStore(), get_metrics_registry())


@lru_cache
def get_knowledge_graph_analytics() -> KnowledgeGraphAnalytics:
    return KnowledgeGraphAnalytics(get_knowledge_graph_metrics_engine())


@lru_cache
def get_policy_engine() -> PolicyEngine:
    return PolicyEngine(InMemoryGovernancePolicyStore())


@lru_cache
def get_knowledge_graph_governance() -> KnowledgeGraphGovernance:
    return KnowledgeGraphGovernance(get_policy_engine(), get_cabinet_governance_engine())


@lru_cache
def get_knowledge_pack_engine() -> KnowledgePackEngine:
    return KnowledgePackEngine(InMemoryKnowledgePackStore(), get_cabinet_knowledge_space())


@lru_cache
def get_copilot_knowledge_bridge() -> CopilotKnowledgeBridge:
    return CopilotKnowledgeBridge(
        get_knowledge_pack_engine(), get_entity_resolution_engine(), get_federation_query_engine()
    )
