from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TimelineEvent:
    """A dated event extracted from a document. Always keeps a link back
    to its source document (see docs/14-document-intelligence.md)."""

    date: str
    description: str
    document_id: str
    confidence: float
