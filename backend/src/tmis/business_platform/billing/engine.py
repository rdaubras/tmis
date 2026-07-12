from tmis.business_platform.plans.engine import PlanCatalog
from tmis.business_platform.pricing.engine import PricingEngine
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.schemas import FeeType, Invoice


class SubscriptionBillingEngine:
    """Bills a firm's SaaS Business Platform subscription — composes
    `cabinet_os.billing.BillingEngine` directly (Sprint 9's full
    quote/invoice/credit-note/payment engine, already
    payment-provider-agnostic behind `PaymentGatewayPort`) rather than
    reimplementing invoicing. This module only knows *what* to bill
    (one line per subscription period, price sourced from
    `pricing.PricingEngine`); `cabinet_os.billing` still owns *how* an
    invoice is built, issued and paid."""

    def __init__(
        self,
        billing: BillingEngine,
        subscriptions: SubscriptionEngine,
        plans: PlanCatalog,
        pricing: PricingEngine,
        discount_percent: float = 0.0,
    ) -> None:
        self._billing = billing
        self._subscriptions = subscriptions
        self._plans = plans
        self._pricing = pricing
        self._discount_percent = discount_percent

    def invoice_for_subscription(self, firm_id: str) -> Invoice:
        subscription = self._subscriptions.get(firm_id)
        plan = self._plans.get(subscription.plan_id)
        price = self._pricing.price_for(plan, subscription.billing_cycle, self._discount_percent)
        invoice = self._billing.create_invoice(firm_id, client_id=firm_id)
        self._billing.add_invoice_line(
            invoice.id,
            description=f"Abonnement {plan.name.value} ({subscription.billing_cycle.value})",
            quantity=1,
            unit_price=price.final_amount,
            fee_type=FeeType.FLAT_FEE,
        )
        return self._billing.issue_invoice(invoice.id)
