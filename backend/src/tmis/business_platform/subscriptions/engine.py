from datetime import UTC, datetime, timedelta

from tmis.business_platform.plans.engine import PlanCatalog
from tmis.business_platform.subscriptions.ports import SubscriptionStorePort
from tmis.business_platform.subscriptions.schemas import (
    BillingCycle,
    Subscription,
    SubscriptionStatus,
    default_trial_end,
    new_subscription_id,
    period_end_for_cycle,
)


class SubscriptionEngine:
    """The SaaS Business Platform's subscription lifecycle — composes
    `plans.PlanCatalog` rather than embedding plan data directly, so a
    subscription always resolves against the exact plan version it was
    sold under."""

    def __init__(self, store: SubscriptionStorePort, plans: PlanCatalog) -> None:
        self._store = store
        self._plans = plans

    def start_trial(self, firm_id: str, plan_id: str) -> Subscription:
        self._plans.get(plan_id)  # raises KeyError if the plan doesn't exist
        now = datetime.now(UTC)
        subscription = Subscription(
            id=new_subscription_id(),
            firm_id=firm_id,
            plan_id=plan_id,
            status=SubscriptionStatus.TRIAL,
            started_at=now,
            trial_ends_at=default_trial_end(now),
        )
        self._store.save(subscription)
        return subscription

    def activate(
        self, firm_id: str, billing_cycle: BillingCycle = BillingCycle.MONTHLY
    ) -> Subscription:
        subscription = self._require(firm_id)
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.billing_cycle = billing_cycle
        subscription.current_period_end = period_end_for_cycle(billing_cycle)
        self._store.save(subscription)
        return subscription

    def change_plan(self, firm_id: str, plan_id: str) -> Subscription:
        self._plans.get(plan_id)
        subscription = self._require(firm_id)
        subscription.plan_id = plan_id
        self._store.save(subscription)
        return subscription

    def mark_past_due(self, firm_id: str) -> Subscription:
        subscription = self._require(firm_id)
        subscription.status = SubscriptionStatus.PAST_DUE
        self._store.save(subscription)
        return subscription

    def cancel(self, firm_id: str) -> Subscription:
        subscription = self._require(firm_id)
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = datetime.now(UTC)
        self._store.save(subscription)
        return subscription

    def expire(self, firm_id: str) -> Subscription:
        subscription = self._require(firm_id)
        subscription.status = SubscriptionStatus.EXPIRED
        self._store.save(subscription)
        return subscription

    def extend_trial(self, firm_id: str, extra_days: int) -> Subscription:
        subscription = self._require(firm_id)
        base = subscription.trial_ends_at or datetime.now(UTC)
        subscription.trial_ends_at = base + timedelta(days=extra_days)
        self._store.save(subscription)
        return subscription

    def advance_period(self, firm_id: str) -> Subscription:
        subscription = self._require(firm_id)
        subscription.current_period_end = period_end_for_cycle(subscription.billing_cycle)
        self._store.save(subscription)
        return subscription

    def is_trial_expired(self, firm_id: str, *, now: datetime | None = None) -> bool:
        subscription = self._require(firm_id)
        if subscription.status is not SubscriptionStatus.TRIAL:
            return False
        if subscription.trial_ends_at is None:
            return False
        return (now or datetime.now(UTC)) > subscription.trial_ends_at

    def get(self, firm_id: str) -> Subscription:
        return self._require(firm_id)

    def list_all(self) -> list[Subscription]:
        return self._store.list_all()

    def _require(self, firm_id: str) -> Subscription:
        subscription = self._store.get(firm_id)
        if subscription is None:
            raise KeyError(firm_id)
        return subscription
