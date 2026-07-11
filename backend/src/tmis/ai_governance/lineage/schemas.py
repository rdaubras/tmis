import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_lineage_record_id() -> str:
    return f"lin-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class LineageRecord:
    """Mirrors `tmis.cabinet_knowledge.lineage.LineageRecord`'s shape
    (origin refs + optional revision pointer), adapted from knowledge
    objects to AI productions."""

    id: str
    firm_id: str
    production_id: str
    source_refs: tuple[str, ...]
    actor: str
    revised_from_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class LineageExplanation:
    """Answers "d'où vient cette production, et de quelle production
    antérieure est-elle issue" in a single object — `revision_chain`
    is ordered from the earliest ancestor to `production_id` itself."""

    production_id: str
    origin_records: tuple[LineageRecord, ...]
    revision_chain: tuple[str, ...]
