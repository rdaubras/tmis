from typing import Protocol

from tmis.document_intelligence.schemas.record import DocumentRecord


class ExportPort(Protocol):
    def export(self, record: DocumentRecord) -> str: ...
