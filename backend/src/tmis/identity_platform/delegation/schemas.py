import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.identity_platform.permissions.schemas import Permission


def new_delegation_id() -> str:
    return f"deleg-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class Delegation:
    """A time-bound grant of a subset of the delegator's permissions
    to another user — "limitées dans le temps, traçables et
    révocables" (sprint requirement)."""

    id: str
    firm_id: str
    delegator_id: str
    delegate_id: str
    permissions: frozenset[Permission]
    ends_at: datetime
    starts_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    revoked: bool = False
