from typing import Protocol

from tmis.legal_research.queries.schemas import ResearchQuery


class QueryEnginePort(Protocol):
    """Port implemented by every interchangeable query-preparation engine
    (normalization, language detection, keyword extraction, expansion)."""

    def build(
        self, raw_text: str, filters: dict[str, object] | None = None
    ) -> ResearchQuery: ...
