from typing import Protocol

from tmis.legal_drafting.citations.schemas import DraftCitation


class CitationFormatterPort(Protocol):
    """Port implemented by every interchangeable draft-citation formatter."""

    def format(self, citation: DraftCitation) -> str: ...
