import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

_DEFAULT_SESSION_TTL = timedelta(hours=8)


def new_session_id() -> str:
    return f"sess-{uuid.uuid4().hex[:16]}"


def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def default_session_expiry() -> datetime:
    return datetime.now(UTC) + _DEFAULT_SESSION_TTL


@dataclass(slots=True)
class Session:
    id: str
    firm_id: str
    user_id: str
    device_id: str | None
    refresh_token: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime = field(default_factory=default_session_expiry)
    revoked: bool = False
