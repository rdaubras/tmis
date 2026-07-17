from typing import Protocol

from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.citations.schemas import ResearchCitation
from tmis.legal_research.queries.schemas import ResearchQuery
from tmis.legal_research.search.schemas import RelevanceScores, ResearchResponse


class ResearchSearchPort(Protocol):
    """Port implemented by every interchangeable search execution
    strategy (lexical-only, hybrid text + vectors, ...)."""

    async def execute(
        self, query: ResearchQuery, *, connector_names: list[str] | None = None
    ) -> tuple[list[ConnectorDocument], list[str], dict[str, RelevanceScores]]:
        """Runs the search and returns (documents, connectors actually
        used, a document-id -> `RelevanceScores` map for re-ranking)."""
        ...


class ResearchSearchStorePort(Protocol):
    """Port implemented by every interchangeable store for a completed
    search's response + citations (ADR-RESEARCH-02, see
    docs/21-legal-research.md) — what `ResearchOrchestrator._responses`/
    `_citations` used to keep on the singleton itself, before the
    orchestrator became a per-request object. A later `GET /searches/
    {search_id}` (a fresh request, a fresh orchestrator) can only find a
    past search again through this port."""

    def save(
        self,
        response: ResearchResponse,
        citations: tuple[ResearchCitation, ...],
        *,
        user_id: str | None = None,
        case_id: str | None = None,
    ) -> None: ...

    def get(self, search_id: str) -> ResearchResponse | None: ...

    def get_citations(self, search_id: str) -> tuple[ResearchCitation, ...] | None: ...
