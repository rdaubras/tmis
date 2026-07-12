from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.schemas import BillingCycle, Subscription


class TrialEngine:
    """Trial start/extend/convert/expire — a thin facade over
    `subscriptions.SubscriptionEngine` (never reimplements the
    subscription state machine, only orchestrates the trial-specific
    transitions on top of it)."""

    def __init__(self, subscriptions: SubscriptionEngine) -> None:
        self._subscriptions = subscriptions

    def start(self, firm_id: str, plan_id: str) -> Subscription:
        return self._subscriptions.start_trial(firm_id, plan_id)

    def extend(self, firm_id: str, extra_days: int) -> Subscription:
        return self._subscriptions.extend_trial(firm_id, extra_days)

    def convert_to_paid(
        self, firm_id: str, billing_cycle: BillingCycle = BillingCycle.MONTHLY
    ) -> Subscription:
        return self._subscriptions.activate(firm_id, billing_cycle)

    def expire_if_needed(self, firm_id: str) -> Subscription | None:
        if self._subscriptions.is_trial_expired(firm_id):
            return self._subscriptions.expire(firm_id)
        return None
