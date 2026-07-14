from dataclasses import dataclass

from tmis.cabinet_knowledge.approval.engine import ApprovalEngine
from tmis.cabinet_knowledge.validation.engine import ValidationEngine
from tmis.legal_copilot_framework.context_engine.engine import ContextEngine
from tmis.legal_knowledge_graph.analytics.engine import GraphAnalyticsEngine
from tmis.legal_knowledge_graph.copilot_bridge.engine import KnowledgeGraphQueryEngine
from tmis.legal_knowledge_graph.entity_resolution.engine import EntityResolutionEngine
from tmis.legal_knowledge_graph.governance.engine import GraphAccessPolicyEngine
from tmis.legal_knowledge_graph.graph_core.engine import GraphEngine
from tmis.legal_knowledge_graph.human_validation.engine import GraphFeedbackEngine
from tmis.legal_knowledge_graph.ingestion.engine import KnowledgeIngestionPipeline
from tmis.legal_knowledge_graph.quality.engine import GraphQualityEngine
from tmis.legal_knowledge_graph.semantic_engine.engine import SemanticEngine


@dataclass(frozen=True, slots=True)
class LkgDemoDeps:
    """Everything the Phase 11 demo scenario needs, bundled so its
    signature stays short. Every field is an engine this sprint (or an
    earlier one) already built — the demo composes them, it never
    constructs its own storage."""

    graph: GraphEngine
    semantic: SemanticEngine
    ingestion: KnowledgeIngestionPipeline
    validation: ValidationEngine
    approval: ApprovalEngine
    entity_resolution: EntityResolutionEngine
    feedback: GraphFeedbackEngine
    governance: GraphAccessPolicyEngine
    quality: GraphQualityEngine
    analytics: GraphAnalyticsEngine
    copilot_query: KnowledgeGraphQueryEngine
    context_engine: ContextEngine
