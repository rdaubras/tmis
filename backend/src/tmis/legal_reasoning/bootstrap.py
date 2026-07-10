from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.legal_reasoning.reasoner.adapters import CaseIntelligenceCaseAdapter, LegalResearchAdapter
from tmis.legal_reasoning.reasoner.orchestrator import ReasoningOrchestrator
from tmis.legal_research.bootstrap import get_research_orchestrator


@lru_cache
def get_reasoning_orchestrator() -> ReasoningOrchestrator:
    """Process-wide `ReasoningOrchestrator` singleton (see
    docs/25-legal-reasoning.md), built directly on top of the shared
    `TMISKernel`, `CaseIntelligenceWorkflow` (Sprint 4) and
    `ResearchOrchestrator` (Sprint 5) — the LRE² never re-implements case
    analysis or documentary search, it composes what already exists.
    """
    kernel = get_kernel()
    case_workflow = get_case_intelligence_workflow()
    research_orchestrator = get_research_orchestrator()

    return ReasoningOrchestrator(
        case_port=CaseIntelligenceCaseAdapter(case_workflow),
        research_port=LegalResearchAdapter(research_orchestrator),
        kernel=kernel,
        event_bus=kernel.event_bus,
    )
