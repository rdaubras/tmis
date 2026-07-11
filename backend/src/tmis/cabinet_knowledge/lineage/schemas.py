import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.cabinet_knowledge.governance.schemas import GovernanceEvent


def new_lineage_record_id() -> str:
    return f"lin-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class LineageRecord:
    id: str
    firm_id: str
    knowledge_object_id: str
    source_refs: tuple[str, ...]
    actor: str
    revised_from_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class LineageExplanation:
    """Answers the sprint's "chaque connaissance doit pouvoir
    expliquer : son origine ; les documents utilisés ; les
    validations ; les révisions ; les versions" in a single object."""

    knowledge_object_id: str
    current_version: int
    origin_records: tuple[LineageRecord, ...]
    governance_events: tuple[GovernanceEvent, ...]
