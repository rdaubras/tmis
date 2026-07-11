from functools import lru_cache

from tmis.ai_governance.audit.engine import AIAuditEngine
from tmis.ai_governance.audit.store import InMemoryAIAuditStore
from tmis.ai_governance.bias_detection.engine import BiasDetectionEngine
from tmis.ai_governance.compliance.engine import ComplianceEngine
from tmis.ai_governance.confidence.engine import GovernanceConfidenceEngine
from tmis.ai_governance.decision_records.engine import DecisionRecordEngine
from tmis.ai_governance.decision_records.store import InMemoryDecisionRecordStore
from tmis.ai_governance.ethics.engine import EthicsEngine
from tmis.ai_governance.evaluation.engine import GovernanceEvaluator
from tmis.ai_governance.evaluation.store import InMemoryGovernanceMetricsSink
from tmis.ai_governance.events import GovernanceEventBus
from tmis.ai_governance.explainability.engine import ExplainabilityEngine
from tmis.ai_governance.explainability.store import InMemoryExplainabilityStore
from tmis.ai_governance.hallucination_detection.engine import HallucinationDetectionEngine
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.ai_governance.lineage.engine import LineageEngine
from tmis.ai_governance.lineage.store import InMemoryLineageStore
from tmis.ai_governance.overview import AIGovernancePlatform
from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.store import InMemoryGovernancePolicyStore
from tmis.ai_governance.provenance.engine import ProvenanceEngine
from tmis.ai_governance.provenance.store import InMemoryProvenanceStore
from tmis.ai_governance.quality.engine import GovernanceQualityEngine
from tmis.ai_governance.reasoning_chain.engine import ReasoningChainEngine
from tmis.ai_governance.reasoning_chain.store import InMemoryReasoningChainStore
from tmis.ai_governance.reporting.engine import ReportGenerator
from tmis.ai_governance.risk_engine.engine import RiskEngine
from tmis.ai_governance.traceability.engine import TraceabilityEngine
from tmis.ai_governance.traceability.store import InMemoryTraceStore


@lru_cache
def get_governance_event_bus() -> GovernanceEventBus:
    """Process-wide composition root for `tmis.ai_governance` (see
    docs/80-architecture-ai-governance.md)."""
    return GovernanceEventBus()


@lru_cache
def get_reasoning_chain_engine() -> ReasoningChainEngine:
    return ReasoningChainEngine(InMemoryReasoningChainStore())


@lru_cache
def get_decision_record_engine() -> DecisionRecordEngine:
    return DecisionRecordEngine(InMemoryDecisionRecordStore())


@lru_cache
def get_confidence_engine() -> GovernanceConfidenceEngine:
    return GovernanceConfidenceEngine()


@lru_cache
def get_risk_engine() -> RiskEngine:
    return RiskEngine()


@lru_cache
def get_explainability_engine() -> ExplainabilityEngine:
    return ExplainabilityEngine(InMemoryExplainabilityStore())


@lru_cache
def get_provenance_engine() -> ProvenanceEngine:
    return ProvenanceEngine(InMemoryProvenanceStore())


@lru_cache
def get_traceability_engine() -> TraceabilityEngine:
    return TraceabilityEngine(InMemoryTraceStore())


@lru_cache
def get_lineage_engine() -> LineageEngine:
    return LineageEngine(InMemoryLineageStore())


@lru_cache
def get_bias_detection_engine() -> BiasDetectionEngine:
    return BiasDetectionEngine()


@lru_cache
def get_hallucination_detection_engine() -> HallucinationDetectionEngine:
    return HallucinationDetectionEngine()


@lru_cache
def get_policy_engine() -> PolicyEngine:
    return PolicyEngine(InMemoryGovernancePolicyStore())


@lru_cache
def get_human_validation_engine() -> HumanValidationEngine:
    return HumanValidationEngine(InMemoryValidationStore())


@lru_cache
def get_ai_audit_engine() -> AIAuditEngine:
    return AIAuditEngine(InMemoryAIAuditStore())


@lru_cache
def get_compliance_engine() -> ComplianceEngine:
    return ComplianceEngine()


@lru_cache
def get_ethics_engine() -> EthicsEngine:
    return EthicsEngine()


@lru_cache
def get_quality_engine() -> GovernanceQualityEngine:
    return GovernanceQualityEngine()


@lru_cache
def get_governance_metrics_sink() -> InMemoryGovernanceMetricsSink:
    return InMemoryGovernanceMetricsSink()


@lru_cache
def get_governance_evaluator() -> GovernanceEvaluator:
    return GovernanceEvaluator([get_governance_metrics_sink()])


@lru_cache
def get_report_generator() -> ReportGenerator:
    return ReportGenerator()


@lru_cache
def get_ai_governance_platform() -> AIGovernancePlatform:
    return AIGovernancePlatform(
        get_reasoning_chain_engine(),
        get_provenance_engine(),
        get_traceability_engine(),
        get_decision_record_engine(),
        get_human_validation_engine(),
        get_lineage_engine(),
        get_explainability_engine(),
    )
