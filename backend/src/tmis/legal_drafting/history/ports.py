from typing import Protocol

from tmis.legal_drafting.history.schemas import DraftHistoryActionType, DraftHistoryEntry


class DraftHistoryPort(Protocol):
    """Port implemented by every interchangeable draft history store."""

    def record(
        self,
        document_id: str,
        action: DraftHistoryActionType,
        author: str | None = None,
        details: str = "",
    ) -> DraftHistoryEntry: ...

    def list_for_document(self, document_id: str) -> list[DraftHistoryEntry]: ...
