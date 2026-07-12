from tmis.business_platform.billing.engine import SubscriptionBillingEngine
from tmis.business_platform.invoicing.engine import InvoicingEngine
from tmis.business_platform.payments.engine import PaymentEngine
from tmis.business_platform.plans.engine import PlanCatalog, seed_default_catalog
from tmis.business_platform.plans.schemas import PlanName
from tmis.business_platform.plans.store import InMemoryPlanStore
from tmis.business_platform.pricing.engine import PricingEngine
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.subscriptions.schemas import BillingCycle
from tmis.business_platform.subscriptions.store import InMemorySubscriptionStore
from tmis.cabinet_os.billing.engine import BillingEngine
from tmis.cabinet_os.billing.gateway import ManualPaymentGateway, NoOpAccountingExport
from tmis.cabinet_os.billing.schemas import PaymentMethod
from tmis.cabinet_os.billing.store import (
    InMemoryCreditNoteStore,
    InMemoryInvoiceStore,
    InMemoryPaymentStore,
    InMemoryQuoteStore,
)


def _wired_firm(firm_id: str = "firm-1") -> tuple[SubscriptionEngine, PlanCatalog, BillingEngine]:
    catalog = PlanCatalog(InMemoryPlanStore())
    seed_default_catalog(catalog)
    subs = SubscriptionEngine(InMemorySubscriptionStore(), catalog)
    plan = catalog.latest(PlanName.PROFESSIONAL)
    subs.start_trial(firm_id, plan.id)
    subs.activate(firm_id, BillingCycle.MONTHLY)
    billing = BillingEngine(
        InMemoryQuoteStore(),
        InMemoryInvoiceStore(),
        InMemoryCreditNoteStore(),
        InMemoryPaymentStore(),
        ManualPaymentGateway(),
        NoOpAccountingExport(),
    )
    return subs, catalog, billing


def test_pricing_engine_applies_discount() -> None:
    catalog = PlanCatalog(InMemoryPlanStore())
    seed_default_catalog(catalog)
    plan = catalog.latest(PlanName.PROFESSIONAL)
    pricing = PricingEngine()

    quote = pricing.price_for(plan, BillingCycle.MONTHLY, discount_percent=10.0)

    assert quote.final_amount == plan.monthly_price_usd * 0.9


def test_subscription_billing_engine_issues_invoice_with_plan_price() -> None:
    subs, catalog, billing = _wired_firm()
    engine = SubscriptionBillingEngine(billing, subs, catalog, PricingEngine())

    invoice = engine.invoice_for_subscription("firm-1")

    plan = catalog.latest(PlanName.PROFESSIONAL)
    assert invoice.firm_id == "firm-1"
    assert billing.total_due(invoice.id) == plan.monthly_price_usd


def test_invoicing_engine_is_due_only_after_period_end() -> None:
    subs, catalog, billing = _wired_firm()
    subscription_billing = SubscriptionBillingEngine(billing, subs, catalog, PricingEngine())
    invoicing = InvoicingEngine(subscription_billing, subs)

    assert invoicing.is_due("firm-1") is False


def test_invoicing_engine_run_billing_cycle_advances_period() -> None:
    subs, catalog, billing = _wired_firm()
    subscription_billing = SubscriptionBillingEngine(billing, subs, catalog, PricingEngine())
    invoicing = InvoicingEngine(subscription_billing, subs)
    original_period_end = subs.get("firm-1").current_period_end

    result = invoicing.run_billing_cycle("firm-1")
    assert result is None  # not due yet

    subs.get("firm-1").current_period_end = original_period_end.replace(year=2000)
    invoice = invoicing.run_billing_cycle("firm-1")

    assert invoice is not None
    assert subs.get("firm-1").current_period_end != original_period_end


def test_payment_engine_records_payment_reducing_total_due() -> None:
    subs, catalog, billing = _wired_firm()
    subscription_billing = SubscriptionBillingEngine(billing, subs, catalog, PricingEngine())
    payments = PaymentEngine(billing)
    invoice = subscription_billing.invoice_for_subscription("firm-1")

    payments.record_payment(
        invoice.id, amount=payments.total_due(invoice.id), method=PaymentMethod.BANK_TRANSFER
    )

    assert payments.total_due(invoice.id) == 0.0
