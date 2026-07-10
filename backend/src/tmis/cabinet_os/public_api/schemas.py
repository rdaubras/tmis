from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ApiScope(str, Enum):
    """Broad resource-area scopes — deliberately coarse-grained
    (see docs/44-guide-api-publique.md); narrower scopes can be added
    without touching anything that already checks membership in a
    `frozenset[ApiScope]`."""

    READ_CLIENTS = "read:clients"
    WRITE_CLIENTS = "write:clients"
    READ_CASES = "read:cases"
    WRITE_CASES = "write:cases"
    READ_BILLING = "read:billing"
    WRITE_BILLING = "write:billing"
    READ_DOCUMENTS = "read:documents"
    WRITE_DOCUMENTS = "write:documents"
    ADMIN = "admin"


@dataclass(slots=True)
class ApiKey:
    """An issued API key — only the salted hash is stored; the raw
    key is returned once, at issuance, and never persisted (see
    docs/44-guide-api-publique.md — API Keys)."""

    id: str
    firm_id: str
    name: str
    key_hash: str
    prefix: str
    scopes: frozenset[ApiScope]
    created_at: datetime
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None


@dataclass(slots=True)
class OAuthClient:
    """A registered OAuth2 client (client-credentials grant this
    sprint — see docs/44-guide-api-publique.md — OAuth, known
    limitation: no user-delegated authorization-code flow yet)."""

    id: str
    firm_id: str
    client_id: str
    client_secret_hash: str
    redirect_uris: list[str]
    scopes: frozenset[ApiScope]
    created_at: datetime


@dataclass(frozen=True, slots=True)
class OAuthToken:
    token: str
    client_id: str
    firm_id: str
    scopes: frozenset[ApiScope]
    issued_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class RateLimitPolicy:
    requests_per_minute: int = 60
    burst: int = 10


@dataclass(frozen=True, slots=True)
class ApiVersionInfo:
    version: str
    deprecated: bool = False
    sunset_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RateLimitResult:
    allowed: bool
    remaining: int
    retry_after_seconds: float = 0.0
    limit: int = field(default=0)
