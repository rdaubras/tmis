from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ApprovalMode(str, Enum):
    """SINGLE: any one approver deciding APPROVE settles the request.
    MULTIPLE: every listed approver must independently decide APPROVE."""

    SINGLE = "single"
    MULTIPLE = "multiple"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ApprovalDecisionType(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    """One approver's decision — appended to `ApprovalRequest.history`,
    never overwritten or removed (see docs/38-guide-validations.md)."""

    approver_id: str
    decision: ApprovalDecisionType
    comment: str | None
    decided_at: datetime


@dataclass(slots=True)
class ApprovalRequest:
    id: str
    workspace_id: str
    target_type: str
    target_id: str
    requested_by: str
    approver_ids: tuple[str, ...]
    mode: ApprovalMode
    status: ApprovalStatus = ApprovalStatus.PENDING
    history: list[ApprovalDecision] = field(default_factory=list)
    created_at: datetime | None = None
