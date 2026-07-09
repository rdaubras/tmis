import uuid
from dataclasses import dataclass
from enum import Enum


class CaseStatus(str, Enum):
    OPEN = "open"
    ANALYSIS_IN_PROGRESS = "analysis_in_progress"
    DRAFTING_IN_PROGRESS = "drafting_in_progress"
    PENDING_VALIDATION = "pending_validation"
    CLOSED = "closed"
    ARCHIVED = "archived"


@dataclass
class Case:
    """Aggregate root of the `case` bounded context.

    Pivot entity referenced by document, timeline, contract, drafting and
    legal_research contexts (see docs/04-domain-driven-design.md).
    """

    id: uuid.UUID
    firm_id: uuid.UUID
    title: str
    status: CaseStatus = CaseStatus.OPEN
