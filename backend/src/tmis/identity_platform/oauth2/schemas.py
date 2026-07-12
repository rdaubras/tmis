import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


def new_client_id() -> str:
    return f"client-{uuid.uuid4().hex[:16]}"


@dataclass(frozen=True, slots=True)
class OAuth2Client:
    client_id: str
    firm_id: str
    redirect_uris: tuple[str, ...]
    client_secret_hash: str


@dataclass(slots=True)
class AuthorizationCodeRecord:
    code: str
    client_id: str
    user_id: str
    firm_id: str
    redirect_uri: str
    expires_at: datetime
    used: bool = False


def new_authorization_code_expiry() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class TokenPair:
    access_token: str
    refresh_token: str
    user_id: str
    firm_id: str
    token_type: str = "Bearer"
    expires_in: int = 3600


class OAuth2Error(Exception):
    pass
