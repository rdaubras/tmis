from typing import Protocol

from tmis.legal_drafting.documents.schemas import Document
from tmis.legal_drafting.export.schemas import ExportResult


class ExporterPort(Protocol):
    """Port implemented by every interchangeable document exporter."""

    def export(self, document: Document) -> ExportResult: ...
