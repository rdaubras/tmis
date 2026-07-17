from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.legal_reasoning.reasoner.adapters import CaseIntelligenceCaseAdapter, LegalResearchAdapter
from tmis.legal_reasoning.reasoner.orchestrator import ReasoningOrchestrator
from tmis.legal_research.bootstrap import get_shared_research_orchestrator


@lru_cache
def get_reasoning_orchestrator() -> ReasoningOrchestrator:
    """Process-wide `ReasoningOrchestrator` singleton (see
    docs/25-legal-reasoning.md), built directly on top of the shared
    `TMISKernel`, `CaseIntelligenceWorkflow` (Sprint 4) and
    `ResearchOrchestrator` (Sprint 5) — the LRE² never re-implements case
    analysis or documentary search, it composes what already exists.

    Uses `get_shared_research_orchestrator`, not the firm-scoped
    `get_research_orchestrator` (ADR-RESEARCH-02,
    docs/21-legal-research.md): this accessor has no request to derive a
    `firm_id`/`Session` from, and `legal_reasoning` itself has not been
    through its own firm-isolation pass yet — giving it a fabricated
    `firm_id` here would look isolated without being isolated.
    """
    kernel = get_kernel()
    case_workflow = get_case_intelligence_workflow()
    research_orchestrator = get_shared_research_orchestrator()

    return ReasoningOrchestrator(
        case_port=CaseIntelligenceCaseAdapter(case_workflow),
        research_port=LegalResearchAdapter(research_orchestrator),
        kernel=kernel,
        event_bus=kernel.event_bus,
    )
