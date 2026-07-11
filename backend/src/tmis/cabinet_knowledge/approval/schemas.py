import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_approval_record_id() -> str:
    return f"appr-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class ApprovalRecord:
    id: str
    firm_id: str
    knowledge_object_id: str
    approver: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
