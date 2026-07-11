from dataclasses import dataclass, field

from tmis.ai_governance.bias_detection.schemas import BiasFinding
from tmis.ai_governance.confidence.schemas import GovernanceConfidenceScore
from tmis.ai_governance.decision_records.engine import DecisionRecordEngine
from tmis.ai_governance.decision_records.schemas import DecisionRecord
from tmis.ai_governance.ethics.schemas import EthicsFinding
from tmis.ai_governance.explainability.engine import ExplainabilityEngine
from tmis.ai_governance.explainability.schemas import ExplainabilityReport
from tmis.ai_governance.hallucination_detection.schemas import HallucinationAlert
from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationRequest
from tmis.ai_governance.lineage.engine import LineageEngine
from tmis.ai_governance.lineage.schemas import LineageExplanation
from tmis.ai_governance.provenance.engine import ProvenanceEngine
from tmis.ai_governance.provenance.schemas import ProvenanceRecord
from tmis.ai_governance.reasoning_chain.engine import ReasoningChainEngine
from tmis.ai_governance.reasoning_chain.schemas import ReasoningChain
from tmis.ai_governance.risk_engine.schemas import RiskFinding
from tmis.ai_governance.traceability.engine import TraceabilityEngine
from tmis.ai_governance.traceability.schemas import TraceEntry


@dataclass(frozen=True, slots=True)
class ProductionGovernanceOverview:
    """Answers, in a single read, every question the sprint's Vision
    section asks of one AI production: pourquoi cette réponse, quels
    faits, quelles sources, quels agents, quels modèles, quelles
    hypothèses, quels risques, quel niveau de confiance, quelles
    validations humaines. "Toutes ces informations doivent être
    consultables" (sprint requirement)."""

    production_id: str
    reasoning_chain: ReasoningChain
    provenance: tuple[ProvenanceRecord, ...]
    trace: tuple[TraceEntry, ...]
    decisions: tuple[DecisionRecord, ...]
    validations: tuple[ValidationRequest, ...]
    lineage: LineageExplanation
    explainability: ExplainabilityReport | None = None
    confidence: GovernanceConfidenceScore | None = None
    risks: tuple[RiskFinding, ...] = field(default_factory=tuple)
    bias_findings: tuple[BiasFinding, ...] = field(default_factory=tuple)
    hallucination_alerts: tuple[HallucinationAlert, ...] = field(default_factory=tuple)
    ethics_findings: tuple[EthicsFinding, ...] = field(default_factory=tuple)


class AIGovernancePlatform:
    """The single entry point every business module is expected to
    consult for "peut-on expliquer, tracer, gouverner et auditer cette
    production ?" — per the sprint's constraint that every AI
    production must be explainable, traceable, governed, and
    auditable. Composes the already-persisted engines
    (`reasoning_chain`, `provenance`, `traceability`,
    `decision_records`, `human_validation`, `lineage`,
    `explainability`) into one read; confidence, risks, bias,
    hallucination, and ethics findings are supplied by the caller
    (they are typically computed once per production and are cheap to
    pass through, keeping this facade free of a dependency on every
    detector engine's internal storage)."""

    def __init__(
        self,
        reasoning_chain: ReasoningChainEngine,
        provenance: ProvenanceEngine,
        traceability: TraceabilityEngine,
        decision_records: DecisionRecordEngine,
        human_validation: HumanValidationEngine,
        lineage: LineageEngine,
        explainability: ExplainabilityEngine,
    ) -> None:
        self.reasoning_chain = reasoning_chain
        self.provenance = provenance
        self.traceability = traceability
        self.decision_records = decision_records
        self.human_validation = human_validation
        self.lineage = lineage
        self.explainability = explainability

    def overview(
        self,
        firm_id: str,
        production_id: str,
        *,
        confidence: GovernanceConfidenceScore | None = None,
        risks: tuple[RiskFinding, ...] = (),
        bias_findings: tuple[BiasFinding, ...] = (),
        hallucination_alerts: tuple[HallucinationAlert, ...] = (),
        ethics_findings: tuple[EthicsFinding, ...] = (),
    ) -> ProductionGovernanceOverview:
        return ProductionGovernanceOverview(
            production_id=production_id,
            reasoning_chain=self.reasoning_chain.chain_for(firm_id, production_id),
            provenance=tuple(self.provenance.trace(firm_id, production_id)),
            trace=tuple(self.traceability.trace(firm_id, production_id)),
            decisions=tuple(self.decision_records.history(firm_id, production_id)),
            validations=tuple(self.human_validation.history(firm_id, production_id)),
            lineage=self.lineage.explain(firm_id, production_id),
            explainability=self.explainability.latest(firm_id, production_id),
            confidence=confidence,
            risks=risks,
            bias_findings=bias_findings,
            hallucination_alerts=hallucination_alerts,
            ethics_findings=ethics_findings,
        )
