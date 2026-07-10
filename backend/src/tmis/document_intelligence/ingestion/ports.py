from typing import Protocol

from tmis.document_intelligence.schemas.document import IngestedDocument


class DocumentParserPort(Protocol):
    """Port implemented by every interchangeable file-format parser.

    `supports()` lets the `IngestionRegistry` dispatch by content type
    without any parser needing to know about the others (see
    docs/15-guide-nouveau-parser.md for how to add one).
    """

    content_types: tuple[str, ...]

    def supports(self, content_type: str) -> bool: ...

    def parse(self, document_id: str, filename: str, raw_bytes: bytes) -> IngestedDocument: ...


class VirusScanPort(Protocol):
    """Interface-only in Sprint 3 (see docs/14-document-intelligence.md):
    no real antivirus engine is wired yet, but every file passes through
    this port so a real scanner can be plugged in without touching the
    pipeline."""

    def scan(self, filename: str, raw_bytes: bytes) -> None:
        """Raises `VirusDetectedError` if the file is flagged."""
        ...
