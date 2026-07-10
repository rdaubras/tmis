import uuid
from datetime import UTC, datetime, timedelta

from tmis.cabinet_os.subscriptions.ports import SubscriptionStorePort, UsageStorePort
from tmis.cabinet_os.subscriptions.schemas import (
    PlanTier,
    Quota,
    Subscription,
    SubscriptionStatus,
    UsageCounters,
)

_DEFAULT_QUOTAS: dict[PlanTier, Quota] = {
    PlanTier.SOLO: Quota(
        max_users=1, max_ai_requests_per_month=500, max_storage_gb=5.0, options=frozenset()
    ),
    PlanTier.CABINET: Quota(
        max_users=25,
        max_ai_requests_per_month=5_000,
        max_storage_gb=100.0,
        options=frozenset({"advanced_analytics"}),
    ),
    PlanTier.ENTERPRISE: Quota(
        max_users=10_000,
        max_ai_requests_per_month=100_000,
        max_storage_gb=2_000.0,
        options=frozenset({"advanced_analytics", "public_api", "sso"}),
    ),
}


class ConfigurableSubscriptionEngine:
    """Implements `SubscriptionEnginePort` (see docs/39-cabinet-os.md —
    Subscription Engine): Solo/Cabinet/Entreprise plans, each with a
    default `Quota`, fully reconfigurable via the constructor."""

    def __init__(
        self,
        subscription_store: SubscriptionStorePort,
        usage_store: UsageStorePort,
        quotas: dict[PlanTier, Quota] | None = None,
    ) -> None:
        self._subscriptions = subscription_store
        self._usage = usage_store
        self._quotas = dict(quotas or _DEFAULT_QUOTAS)

    def subscribe(self, firm_id: str, plan: PlanTier) -> Subscription:
        now = datetime.now(UTC)
        subscription = Subscription(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            plan=plan,
            quota=self._quotas[plan],
            status=SubscriptionStatus.TRIAL,
            started_at=now,
            trial_ends_at=now + timedelta(days=14),
            current_period_end=now + timedelta(days=30),
        )
        self._subscriptions.save(subscription)
        self._usage.save(UsageCounters(firm_id=firm_id, period_start=now))
        return subscription

    def change_plan(self, firm_id: str, plan: PlanTier) -> Subscription:
        subscription = self._require(firm_id)
        subscription.plan = plan
        subscription.quota = self._quotas[plan]
        self._subscriptions.save(subscription)
        return subscription

    def cancel(self, firm_id: str) -> Subscription:
        subscription = self._require(firm_id)
        subscription.status = SubscriptionStatus.CANCELLED
        self._subscriptions.save(subscription)
        return subscription

    def get(self, firm_id: str) -> Subscription:
        return self._require(firm_id)

    def record_ai_usage(self, firm_id: str, requests: int) -> UsageCounters:
        usage = self._require_usage(firm_id)
        usage.ai_requests_used += requests
        self._usage.save(usage)
        return usage

    def record_storage_usage(self, firm_id: str, gb: float) -> UsageCounters:
        usage = self._require_usage(firm_id)
        usage.storage_gb_used += gb
        self._usage.save(usage)
        return usage

    def set_active_users(self, firm_id: str, count: int) -> UsageCounters:
        usage = self._require_usage(firm_id)
        usage.active_users = count
        self._usage.save(usage)
        return usage

    def has_capacity(self, firm_id: str, dimension: str) -> bool:
        subscription = self._require(firm_id)
        usage = self._require_usage(firm_id)
        quota = subscription.quota
        if dimension == "users":
            return usage.active_users < quota.max_users
        if dimension == "ai_requests":
            return usage.ai_requests_used < quota.max_ai_requests_per_month
        if dimension == "storage":
            return usage.storage_gb_used < quota.max_storage_gb
        raise ValueError(f"Unknown quota dimension: {dimension!r}")

    def usage(self, firm_id: str) -> UsageCounters:
        return self._require_usage(firm_id)

    def _require(self, firm_id: str) -> Subscription:
        subscription = self._subscriptions.get(firm_id)
        if subscription is None:
            raise ValueError(f"No subscription for firm {firm_id!r}")
        return subscription

    def _require_usage(self, firm_id: str) -> UsageCounters:
        usage = self._usage.get(firm_id)
        if usage is None:
            raise ValueError(f"No usage counters for firm {firm_id!r}")
        return usage
