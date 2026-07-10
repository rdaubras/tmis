from typing import Protocol

from tmis.document_intelligence.schemas.record import DocumentRecord


class DocumentStorePort(Protocol):
    """Port implemented by every interchangeable document store backend."""

    def save(self, record: DocumentRecord) -> None: ...

    def get(self, document_id: str) -> DocumentRecord | None: ...

    def list_ids(self) -> list[str]: ...
