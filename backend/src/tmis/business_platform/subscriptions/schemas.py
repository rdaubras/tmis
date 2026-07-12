import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class SubscriptionStatus(StrEnum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class BillingCycle(StrEnum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


def new_subscription_id() -> str:
    return f"sub-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class Subscription:
    """A firm's SaaS Business Platform subscription — the fuller
    subscription aggregate the sprint asks for ("chaque cabinet
    possède son abonnement, ses options, ses quotas..."). Distinct
    from `cabinet_os.subscriptions.Subscription` (Sprint 9): that
    engine's own 3-tier plan+quota+usage bookkeeping keeps working
    for callers that only need it, this one references the richer,
    versioned `plans.Plan` catalog and adds a billing cycle and a
    past-due state a payment-driven subscription needs. `plan_id`
    pins the exact plan *version* sold — publishing a new plan version
    never silently changes what a subscriber agreed to."""

    id: str
    firm_id: str
    plan_id: str
    billing_cycle: BillingCycle = BillingCycle.MONTHLY
    status: SubscriptionStatus = SubscriptionStatus.TRIAL
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    trial_ends_at: datetime | None = None
    current_period_end: datetime | None = None
    cancelled_at: datetime | None = None


def default_trial_end(now: datetime | None = None) -> datetime:
    return (now or datetime.now(UTC)) + timedelta(days=14)


def period_end_for_cycle(cycle: BillingCycle, now: datetime | None = None) -> datetime:
    start = now or datetime.now(UTC)
    return start + (timedelta(days=365) if cycle is BillingCycle.ANNUAL else timedelta(days=30))
