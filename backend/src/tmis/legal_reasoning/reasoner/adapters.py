from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.schemas import ResearchResponse


class CaseIntelligenceCaseAdapter:
    """Implements `ReasoningCasePort` over a `CaseIntelligenceWorkflow`
    (Sprint 4) — the LRE² only ever reads a `CaseProfile` through this
    thin adapter, never re-implementing case analysis."""

    def __init__(self, workflow: CaseIntelligenceWorkflow) -> None:
        self._workflow = workflow

    def get_profile(self, case_id: str) -> CaseProfile | None:
        return self._workflow.case_store.get(case_id)


class LegalResearchAdapter:
    """Implements `ReasoningResearchPort` over a `ResearchOrchestrator`
    (Sprint 5) — the LRE² never queries a connector itself."""

    def __init__(self, orchestrator: ResearchOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def search(self, query: str, *, case_id: str | None = None) -> ResearchResponse:
        return await self._orchestrator.search(query, case_id=case_id)
