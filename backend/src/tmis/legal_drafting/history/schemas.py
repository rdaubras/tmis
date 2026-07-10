from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DraftHistoryActionType(str, Enum):
    CREATED = "created"
    SECTION_REGENERATED = "section_regenerated"
    PARAGRAPH_REGENERATED = "paragraph_regenerated"
    REVIEWED = "reviewed"
    VALIDATED = "validated"
    VERSION_RESTORED = "version_restored"
    EXPORTED = "exported"


@dataclass(frozen=True, slots=True)
class DraftHistoryEntry:
    """One audit-trail entry for a draft — every action taken on it,
    human or automated, kept forever (see docs/28-legal-drafting.md —
    Versioning / Human In The Loop)."""

    id: str
    document_id: str
    action: DraftHistoryActionType
    author: str | None
    timestamp: datetime
    details: str = ""
