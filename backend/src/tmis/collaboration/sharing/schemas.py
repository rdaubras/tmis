from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SharePermission(str, Enum):
    """Limited permissions grantable through a share — deliberately a
    small subset of `tmis.collaboration.permissions.Permission`."""

    READ = "read"
    COMMENT = "comment"


@dataclass(slots=True)
class InternalShare:
    """A share granted directly to another member of the firm — no
    token, access follows normal authentication."""

    id: str
    workspace_id: str
    target_type: str
    target_id: str
    shared_with_member_id: str
    permission: SharePermission
    created_by: str
    created_at: datetime
    revoked_at: datetime | None = None


@dataclass(slots=True)
class ShareLink:
    """A secret-link share for recipients outside the firm's member
    roster — bearer-token access, optionally time-limited, always
    revocable (see docs/33-legal-collaboration.md — Sharing Engine)."""

    id: str
    workspace_id: str
    target_type: str
    target_id: str
    token: str
    permission: SharePermission
    created_by: str
    created_at: datetime
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
