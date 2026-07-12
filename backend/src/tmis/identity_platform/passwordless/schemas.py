import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

_CODE_TTL_MINUTES = 10


def new_challenge_id() -> str:
    return f"pwl-{uuid.uuid4().hex[:12]}"


def generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def new_challenge_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=_CODE_TTL_MINUTES)


@dataclass(slots=True)
class PasswordlessChallenge:
    id: str
    firm_id: str
    user_id: str
    code: str
    expires_at: datetime
    used: bool = False
