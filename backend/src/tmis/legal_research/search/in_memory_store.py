from tmis.legal_research.citations.schemas import ResearchCitation
from tmis.legal_research.search.schemas import ResearchResponse


class InMemoryResearchSearchStore:
    """Implements `ResearchSearchStorePort` with in-memory dicts — the
    exact shape `ResearchOrchestrator` used to keep on itself before
    ADR-RESEARCH-02 (see docs/21-legal-research.md). Reserved for unit
    tests: the per-request `ResearchOrchestrator` built by
    `tmis.legal_research.bootstrap.get_research_orchestrator` always
    receives `SQLAlchemyResearchSearchStore` instead, so a search
    survives past the request that created it."""

    def __init__(self) -> None:
        self._responses: dict[str, ResearchResponse] = {}
        self._citations: dict[str, tuple[ResearchCitation, ...]] = {}

    def save(
        self,
        response: ResearchResponse,
        citations: tuple[ResearchCitation, ...],
        *,
        user_id: str | None = None,
        case_id: str | None = None,
    ) -> None:
        self._responses[response.search_id] = response
        self._citations[response.search_id] = citations

    def get(self, search_id: str) -> ResearchResponse | None:
        return self._responses.get(search_id)

    def get_citations(self, search_id: str) -> tuple[ResearchCitation, ...] | None:
        return self._citations.get(search_id)
