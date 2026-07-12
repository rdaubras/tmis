from datetime import UTC, datetime

from tmis.business_platform.billing.engine import SubscriptionBillingEngine
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.schemas import SubscriptionStatus
from tmis.cabinet_os.billing.schemas import Invoice


class InvoicingEngine:
    """Decides *when* a subscription is due for a new invoice — never
    the invoice mechanics themselves, which stay owned by
    `billing.SubscriptionBillingEngine`. Supports monthly and annual
    cycles (see `subscriptions.BillingCycle`); a firm on
    `SubscriptionStatus.ACTIVE` past its `current_period_end` is due,
    and generating its invoice also rolls the period forward for the
    next cycle — "facturation mensuelle, annuelle, consommation"
    (sprint requirement; the consumption-based part is layered on top
    by `usage`/`metering`, not duplicated here)."""

    def __init__(
        self, billing: SubscriptionBillingEngine, subscriptions: SubscriptionEngine
    ) -> None:
        self._billing = billing
        self._subscriptions = subscriptions

    def is_due(self, firm_id: str, *, now: datetime | None = None) -> bool:
        subscription = self._subscriptions.get(firm_id)
        if subscription.status is not SubscriptionStatus.ACTIVE:
            return False
        if subscription.current_period_end is None:
            return False
        return (now or datetime.now(UTC)) >= subscription.current_period_end

    def run_billing_cycle(self, firm_id: str) -> Invoice | None:
        if not self.is_due(firm_id):
            return None
        invoice = self._billing.invoice_for_subscription(firm_id)
        self._subscriptions.advance_period(firm_id)
        return invoice
