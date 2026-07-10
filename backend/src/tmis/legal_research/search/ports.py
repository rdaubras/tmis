from typing import Protocol

from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.queries.schemas import ResearchQuery
from tmis.legal_research.search.schemas import RelevanceScores


class ResearchSearchPort(Protocol):
    """Port implemented by every interchangeable search execution
    strategy (lexical-only, hybrid text + vectors, ...)."""

    async def execute(
        self, query: ResearchQuery, *, connector_names: list[str] | None = None
    ) -> tuple[list[ConnectorDocument], list[str], dict[str, RelevanceScores]]:
        """Runs the search and returns (documents, connectors actually
        used, a document-id -> `RelevanceScores` map for re-ranking)."""
        ...
