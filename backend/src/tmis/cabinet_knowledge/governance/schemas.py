import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeStatus

ALLOWED_TRANSITIONS: dict[KnowledgeStatus, frozenset[KnowledgeStatus]] = {
    KnowledgeStatus.DRAFT: frozenset({KnowledgeStatus.IN_REVIEW}),
    KnowledgeStatus.IN_REVIEW: frozenset({KnowledgeStatus.VALIDATED, KnowledgeStatus.DRAFT}),
    KnowledgeStatus.VALIDATED: frozenset({KnowledgeStatus.OBSOLETE, KnowledgeStatus.ARCHIVED}),
    KnowledgeStatus.OBSOLETE: frozenset({KnowledgeStatus.ARCHIVED, KnowledgeStatus.VALIDATED}),
    KnowledgeStatus.ARCHIVED: frozenset(),
}


class InvalidTransitionError(ValueError):
    def __init__(self, from_status: KnowledgeStatus, to_status: KnowledgeStatus) -> None:
        super().__init__(f"Cannot transition from {from_status.value} to {to_status.value}")
        self.from_status = from_status
        self.to_status = to_status


def new_governance_event_id() -> str:
    return f"gov-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class GovernanceEvent:
    id: str
    firm_id: str
    knowledge_object_id: str
    from_status: KnowledgeStatus
    to_status: KnowledgeStatus
    actor: str
    reason: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
