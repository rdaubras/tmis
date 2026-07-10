from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DraftDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    COMMENTED = "commented"


@dataclass(frozen=True, slots=True)
class DraftValidationRecord:
    """One human-in-the-loop decision on a draft — who, what, when, and
    any comment (see docs/28-legal-drafting.md — Human In The Loop).

    Recording an `APPROVED` decision never changes `Document.is_draft`:
    it only moves the internal workflow status forward. TMIS never
    presents the document as legally validated.
    """

    id: str
    document_id: str
    decision: DraftDecision
    author: str
    comment: str | None
    created_at: datetime
