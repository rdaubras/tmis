from dataclasses import dataclass
from datetime import datetime

from tmis.legal_drafting.sections.schemas import Section


@dataclass(frozen=True, slots=True)
class DocumentVersion:
    """An immutable snapshot of a document's sections at one point in
    time (see docs/31-guide-versioning.md)."""

    id: str
    document_id: str
    version_number: int
    sections: tuple[Section, ...]
    author: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class VersionDiff:
    """The result of comparing two versions of the same document, at
    paragraph granularity."""

    version_a: int
    version_b: int
    added_paragraph_ids: tuple[str, ...]
    removed_paragraph_ids: tuple[str, ...]
    changed_paragraph_ids: tuple[str, ...]
