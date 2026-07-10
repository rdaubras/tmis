from typing import Protocol

from tmis.legal_research.citations.schemas import ResearchCitation


class CitationFormatterPort(Protocol):
    """Port implemented by every interchangeable citation output format."""

    def format(self, citation: ResearchCitation) -> str: ...
