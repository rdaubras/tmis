import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ProvenanceGranularity(StrEnum):
    """The sprint's explicit granularity levels: document, section,
    paragraphe, phrase."""

    DOCUMENT = "document"
    SECTION = "section"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"


class SourceType(StrEnum):
    """The sprint's explicit provenance kinds: source documentaire,
    jurisprudence, article de loi, document interne."""

    DOCUMENTARY_SOURCE = "documentary_source"
    JURISPRUDENCE = "jurisprudence"
    STATUTE_ARTICLE = "statute_article"
    INTERNAL_DOCUMENT = "internal_document"


def new_provenance_record_id() -> str:
    return f"prov-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    """Associates one element of a draft (at any granularity) with its
    source, the agent that produced it, and the model that was used —
    the sprint's "chaque affirmation associée à sa provenance"."""

    id: str
    firm_id: str
    production_id: str
    granularity: ProvenanceGranularity
    locator: str
    excerpt: str
    source_type: SourceType
    source_reference: str
    produced_by_agent: str | None = None
    produced_by_model: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
