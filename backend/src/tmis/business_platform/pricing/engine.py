from tmis.business_platform.plans.schemas import Plan
from tmis.business_platform.pricing.schemas import PriceQuote
from tmis.business_platform.subscriptions.schemas import BillingCycle


class PricingEngine:
    """Computes the price of a plan for a billing cycle, with an
    optional discount — "remises" (sprint requirement). Stateless: a
    `PriceQuote` is always derived fresh from the `Plan` passed in,
    never cached, so it can never drift from the plan catalog."""

    def price_for(
        self, plan: Plan, billing_cycle: BillingCycle, discount_percent: float = 0.0
    ) -> PriceQuote:
        base_amount = (
            plan.annual_price_usd
            if billing_cycle is BillingCycle.ANNUAL
            else plan.monthly_price_usd
        )
        final_amount = base_amount * (1 - discount_percent / 100)
        return PriceQuote(
            plan_id=plan.id,
            billing_cycle=billing_cycle,
            base_amount=base_amount,
            discount_percent=discount_percent,
            final_amount=final_amount,
        )
