import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class LicenseType(StrEnum):
    """The four license types the sprint asks for — "licences
    nominatives, flottantes, invité, API". Distinct from
    `platform.licensing.License` (Sprint 10): that engine issues one
    signed, firm-level license bundling seats/features/expiry: this
    module issues individual license *grants*, one per holder (or one
    per checked-out floating seat), each independently assignable,
    revocable and transferable — same "license" concept, finer
    granularity, documented not merged."""

    NOMINATIVE = "nominative"
    FLOATING = "floating"
    GUEST = "guest"
    API = "api"


def new_grant_id() -> str:
    return f"lic-{uuid.uuid4().hex[:12]}"


def default_expiry(days: int = 365, now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + timedelta(days=days)


def now_utc() -> datetime:
    return datetime.now(UTC)


def expiry_in_hours(hours: int, now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + timedelta(hours=hours)


@dataclass(slots=True)
class LicenseGrant:
    """One license unit held by one holder. `holder_id` is a
    `user_id` for NOMINATIVE/GUEST, an API client id for API, and a
    `user_id` for FLOATING only while the seat is checked out (`None`
    once checked back in — the grant record itself stays as history,
    it is never deleted)."""

    id: str
    firm_id: str
    license_type: LicenseType
    holder_id: str | None
    key: str
    granted_at: datetime
    expires_at: datetime
    revoked: bool = False
    transferred_from: str | None = None

    def is_expired(self, *, now: datetime | None = None) -> bool:
        return (now or datetime.now(UTC)) > self.expires_at

    def is_active(self, *, now: datetime | None = None) -> bool:
        return not self.revoked and not self.is_expired(now=now)


@dataclass(slots=True)
class FloatingLicensePool:
    """A firm's shared pool of floating seats — capacity is set
    independently of any individual grant; `LicenseEngine.
    checkout_floating` refuses once every seat is checked out."""

    firm_id: str
    total_seats: int
