from dataclasses import dataclass
from enum import Enum


class IssueStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"


@dataclass(frozen=True, slots=True)
class LegalIssue:
    id: str
    description: str
    related_fact_ids: tuple[str, ...] = ()
    confidence: float = 0.5
    status: IssueStatus = IssueStatus.OPEN
