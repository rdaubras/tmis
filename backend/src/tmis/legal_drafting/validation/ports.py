from typing import Protocol

from tmis.legal_drafting.validation.schemas import DraftDecision, DraftValidationRecord


class DraftValidationServicePort(Protocol):
    """Port implemented by every interchangeable human-in-the-loop
    validation service — distinct from `review` (automated, never a
    human decision) and from `history` (a generic audit trail of every
    action, not just human decisions)."""

    def record(
        self,
        document_id: str,
        decision: DraftDecision,
        author: str,
        comment: str | None = None,
    ) -> DraftValidationRecord: ...

    def list_for_document(self, document_id: str) -> list[DraftValidationRecord]: ...
