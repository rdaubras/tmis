import uuid
from datetime import UTC, datetime

from tmis.legal_drafting.history.schemas import DraftHistoryActionType, DraftHistoryEntry


class InMemoryDraftHistory:
    """Implements `DraftHistoryPort` with an in-memory, append-only
    list — the default deployment for Sprint 7; persistence follows the
    same calendar as the rest of TMIS's engines (Sprint 9)."""

    def __init__(self) -> None:
        self._entries: dict[str, list[DraftHistoryEntry]] = {}

    def record(
        self,
        document_id: str,
        action: DraftHistoryActionType,
        author: str | None = None,
        details: str = "",
    ) -> DraftHistoryEntry:
        entry = DraftHistoryEntry(
            id=str(uuid.uuid4()),
            document_id=document_id,
            action=action,
            author=author,
            timestamp=datetime.now(UTC),
            details=details,
        )
        self._entries.setdefault(document_id, []).append(entry)
        return entry

    def list_for_document(self, document_id: str) -> list[DraftHistoryEntry]:
        return list(self._entries.get(document_id, []))
