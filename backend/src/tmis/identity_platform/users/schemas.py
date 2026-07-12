import uuid
from dataclasses import dataclass
from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEACTIVATED = "deactivated"


def new_user_id() -> str:
    return f"user-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class User:
    """A firm-wide identity — distinct from
    `collaboration.members.Member` (a workspace-scoped invitation).
    One `User` may belong to several workspaces via `Member` records,
    but has exactly one identity here, scoped to one `firm_id`."""

    id: str
    firm_id: str
    email: str
    display_name: str
    team_id: str | None = None
    department_id: str | None = None
    status: UserStatus = UserStatus.ACTIVE
