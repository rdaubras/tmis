import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ValidationDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class ValidationRequestStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


def new_validation_request_id() -> str:
    return f"valreq-{uuid.uuid4()}"


@dataclass(slots=True)
class ValidationRequest:
    id: str
    firm_id: str
    knowledge_object_id: str
    requested_by: str
    requested_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: ValidationRequestStatus = ValidationRequestStatus.PENDING
    reviewer: str | None = None
    decided_at: datetime | None = None
    comment: str | None = None
