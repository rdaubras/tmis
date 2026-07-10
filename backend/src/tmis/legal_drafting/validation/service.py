import uuid
from datetime import UTC, datetime

from tmis.legal_drafting.validation.schemas import DraftDecision, DraftValidationRecord


class HumanInTheLoopService:
    """Implements `DraftValidationServicePort`: records every human
    decision on a draft — approve, reject, or comment — without ever
    deleting a previous record. Approving a draft is an internal
    workflow signal only; it never sets `Document.is_draft` to `False`
    (see docs/28-legal-drafting.md — Human In The Loop)."""

    def __init__(self) -> None:
        self._records: dict[str, list[DraftValidationRecord]] = {}

    def record(
        self,
        document_id: str,
        decision: DraftDecision,
        author: str,
        comment: str | None = None,
    ) -> DraftValidationRecord:
        entry = DraftValidationRecord(
            id=str(uuid.uuid4()),
            document_id=document_id,
            decision=decision,
            author=author,
            comment=comment,
            created_at=datetime.now(UTC),
        )
        self._records.setdefault(document_id, []).append(entry)
        return entry

    def list_for_document(self, document_id: str) -> list[DraftValidationRecord]:
        return list(self._records.get(document_id, []))
