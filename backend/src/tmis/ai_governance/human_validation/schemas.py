import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ValidationMode(StrEnum):
    """SIMPLE: any one approver in the (single) tier settles it.
    MULTIPLE: every approver in the (single) tier must independently
    approve. HIERARCHICAL: an ordered sequence of tiers — each tier
    needs at least one approval before the next tier is considered."""

    SIMPLE = "simple"
    MULTIPLE = "multiple"
    HIERARCHICAL = "hierarchical"


class ValidationStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class ValidationDecisionType(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"


def new_validation_request_id() -> str:
    return f"val-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class ValidationDecisionEntry:
    """One approver's decision — appended to `ValidationRequest.history`,
    never overwritten or removed."""

    approver_id: str
    decision: ValidationDecisionType
    tier: int
    comment: str | None = None
    decided_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class ValidationRequest:
    id: str
    firm_id: str
    production_id: str
    requested_by: str
    approver_tiers: tuple[tuple[str, ...], ...]
    mode: ValidationMode
    status: ValidationStatus = ValidationStatus.PENDING
    history: list[ValidationDecisionEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
