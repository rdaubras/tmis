from typing import Protocol

from tmis.ai.schemas.connector import ConnectorDocument
from tmis.legal_research.search.schemas import RelevanceScores, ResearchResult


class SourceNormalizerPort(Protocol):
    """Port implemented by every interchangeable source normalizer:
    unifies connector-specific metadata into `ResearchResult`, removes
    duplicates, and keeps only the latest version of a document."""

    def normalize(
        self,
        documents: list[ConnectorDocument],
        *,
        scores: dict[str, RelevanceScores] | None = None,
    ) -> list[ResearchResult]: ...
