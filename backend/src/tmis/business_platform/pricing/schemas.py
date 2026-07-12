from dataclasses import dataclass

from tmis.business_platform.subscriptions.schemas import BillingCycle


@dataclass(frozen=True, slots=True)
class PriceQuote:
    """The computed price for one plan, one billing cycle, with any
    discount applied — never stored, always recomputed from the
    current `Plan` at billing time so a discount change or plan
    re-pricing takes effect on the next cycle without a migration."""

    plan_id: str
    billing_cycle: BillingCycle
    base_amount: float
    discount_percent: float
    final_amount: float
    currency: str = "USD"
