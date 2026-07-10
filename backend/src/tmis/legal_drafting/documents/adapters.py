from tmis.case_intelligence.cases.schemas import CaseProfile
from tmis.case_intelligence.workflow.case_workflow import CaseIntelligenceWorkflow
from tmis.legal_reasoning.reasoner.orchestrator import ReasoningOrchestrator
from tmis.legal_reasoning.reasoner.schemas import ReasoningSession
from tmis.legal_research.search.orchestrator import ResearchOrchestrator
from tmis.legal_research.search.schemas import ResearchResponse


class CaseIntelligenceCaseAdapter:
    """Implements `DraftingCasePort` over a `CaseIntelligenceWorkflow`
    (Sprint 4). Mirrors
    `tmis.legal_reasoning.reasoner.adapters.CaseIntelligenceCaseAdapter`."""

    def __init__(self, workflow: CaseIntelligenceWorkflow) -> None:
        self._workflow = workflow

    def get_profile(self, case_id: str) -> CaseProfile | None:
        return self._workflow.case_store.get(case_id)


class LegalResearchAdapter:
    """Implements `DraftingResearchPort` over a `ResearchOrchestrator`
    (Sprint 5)."""

    def __init__(self, orchestrator: ResearchOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def search(self, query: str, *, case_id: str | None = None) -> ResearchResponse:
        return await self._orchestrator.search(query, case_id=case_id)


class LegalReasoningAdapter:
    """Implements `DraftingReasoningPort` over a `ReasoningOrchestrator`
    (Sprint 6)."""

    def __init__(self, orchestrator: ReasoningOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def reason(self, question: str, *, case_id: str | None = None) -> ReasoningSession:
        return await self._orchestrator.reason(question, case_id=case_id)

    def get_session(self, session_id: str) -> ReasoningSession | None:
        return self._orchestrator.get_session(session_id)
