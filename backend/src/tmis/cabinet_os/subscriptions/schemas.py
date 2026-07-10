from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class PlanTier(str, Enum):
    SOLO = "solo"
    CABINET = "cabinet"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class Quota:
    """Per-plan limits (see docs/39-cabinet-os.md — Subscription
    Engine). `options` is an open set of feature-flag strings rather
    than a fixed enum, so a new option never requires a schema change.
    """

    max_users: int
    max_ai_requests_per_month: int
    max_storage_gb: float
    options: frozenset[str] = frozenset()


@dataclass(slots=True)
class Subscription:
    id: str
    firm_id: str
    plan: PlanTier
    quota: Quota
    status: SubscriptionStatus = SubscriptionStatus.TRIAL
    started_at: datetime | None = None
    trial_ends_at: datetime | None = None
    current_period_end: datetime | None = None


@dataclass(slots=True)
class UsageCounters:
    """A firm's current-period consumption against its `Quota`."""

    firm_id: str
    period_start: datetime
    ai_requests_used: int = 0
    storage_gb_used: float = 0.0
    active_users: int = 0
    extra: dict[str, float] = field(default_factory=dict)
