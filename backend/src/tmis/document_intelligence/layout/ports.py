from typing import Protocol

from tmis.document_intelligence.schemas.layout import LayoutBlock


class LayoutAnalyzerPort(Protocol):
    """Port implemented by every interchangeable layout analysis engine."""

    def analyze(self, text: str) -> list[LayoutBlock]: ...
