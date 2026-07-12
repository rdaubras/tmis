from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


@dataclass(slots=True)
class Organization:
    """The enterprise Firm aggregate — the fuller counterpart to
    `cabinet_os.administration.FirmRecord` (a minimal platform-ops
    record: id/name/status only). `firm_id` is the tenant identifier
    used across every bounded context in TMIS; an `Organization` is
    the root of the identity hierarchy (Organisation → Départements →
    Équipes → Utilisateurs)."""

    firm_id: str
    legal_name: str
    status: OrganizationStatus = OrganizationStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
