from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.legal_drafting.documents.adapters import (
    CaseIntelligenceCaseAdapter,
    LegalReasoningAdapter,
    LegalResearchAdapter,
)
from tmis.legal_drafting.documents.orchestrator import DocumentOrchestrator
from tmis.legal_reasoning.bootstrap import get_reasoning_orchestrator
from tmis.legal_research.bootstrap import get_research_orchestrator


@lru_cache
def get_document_orchestrator() -> DocumentOrchestrator:
    """Process-wide `DocumentOrchestrator` singleton (see
    docs/28-legal-drafting.md), built directly on top of the shared
    `TMISKernel`, `CaseIntelligenceWorkflow` (Sprint 4),
    `ResearchOrchestrator` (Sprint 5) and `ReasoningOrchestrator`
    (Sprint 6) — the Legal Drafting Studio never re-implements case
    analysis, documentary search or legal reasoning, it composes what
    already exists into a draft.
    """
    kernel = get_kernel()
    case_workflow = get_case_intelligence_workflow()
    research_orchestrator = get_research_orchestrator()
    reasoning_orchestrator = get_reasoning_orchestrator()

    return DocumentOrchestrator(
        kernel=kernel,
        case_port=CaseIntelligenceCaseAdapter(case_workflow),
        research_port=LegalResearchAdapter(research_orchestrator),
        reasoning_port=LegalReasoningAdapter(reasoning_orchestrator),
    )
