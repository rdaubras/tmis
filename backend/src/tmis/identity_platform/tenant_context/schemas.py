from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class TenantQuota:
    max_users: int = 500
    max_storage_gb: int = 1000
    max_ai_requests_per_day: int = 10000


@dataclass(frozen=True, slots=True)
class TenantBranding:
    display_name: str
    logo_url: str = ""
    primary_color: str = "#0F172A"


@dataclass(slots=True)
class TenantProfile:
    """The enterprise identity — everything about a firm as a tenant,
    beyond the bare `platform.security.tenant_isolation.TenantContext`
    (firm_id/actor_id) — quota, branding, activation state. This is
    the "fuller Firm aggregate" that
    `cabinet_os.administration.FirmRecord`'s docstring explicitly
    deferred to "the future Identity & Firm sprint"."""

    firm_id: str
    quota: TenantQuota = field(default_factory=TenantQuota)
    branding: TenantBranding | None = None
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
