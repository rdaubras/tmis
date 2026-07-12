import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


def new_impersonation_id() -> str:
    return f"imp-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class ImpersonationSession:
    """One "act as this user" support session — "journalisées,
    limitées, visibles, auditables" (sprint requirement). Never
    deleted, only closed (`ended_at` set): the record itself is the
    audit trail an admin's impersonation history is built from."""

    id: str
    firm_id: str
    admin_id: str
    target_user_id: str
    reason: str
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None
