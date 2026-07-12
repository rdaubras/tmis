from tmis.business_platform.analytics.schemas import BusinessDashboard
from tmis.business_platform.modules.engine import ModuleRegistry
from tmis.business_platform.plans.engine import PlanCatalog
from tmis.business_platform.pricing.engine import PricingEngine
from tmis.business_platform.subscriptions.engine import SubscriptionEngine
from tmis.business_platform.usage.engine import UsageEngine
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.ports import CostEntryStorePort


class AnalyticsEngine:
    """Builds the commercial dashboard by composing `subscriptions`,
    `plans`, `pricing`, `usage`, `modules`, and `platform.cost_control`
    (Sprint 10) — never recomputing what those modules already own,
    only aggregating their outputs into one read model."""

    def __init__(
        self,
        subscriptions: SubscriptionEngine,
        plans: PlanCatalog,
        pricing: PricingEngine,
        usage: UsageEngine,
        modules: ModuleRegistry,
        cost_tracker: CostTrackerEngine,
        cost_entries: CostEntryStorePort,
    ) -> None:
        self._subscriptions = subscriptions
        self._plans = plans
        self._pricing = pricing
        self._usage = usage
        self._modules = modules
        self._cost_tracker = cost_tracker
        self._cost_entries = cost_entries

    def build_dashboard(self, firm_id: str) -> BusinessDashboard:
        subscription = self._subscriptions.get(firm_id)
        plan = self._plans.get(subscription.plan_id)
        price = self._pricing.price_for(plan, subscription.billing_cycle)
        mrr = (
            price.final_amount
            if subscription.billing_cycle.value == "monthly"
            else (price.final_amount / 12)
        )

        entries = self._cost_entries.list_for_firm(firm_id)
        paid_entries = [e for e in entries if not e.cache_hit]
        cached_entries = [e for e in entries if e.cache_hit]
        total_ai_cost_usd = sum(e.cost_usd for e in paid_entries)
        avg_cost_per_call = total_ai_cost_usd / len(paid_entries) if paid_entries else 0.0
        cache_savings_usd = avg_cost_per_call * len(cached_entries)

        return BusinessDashboard(
            firm_id=firm_id,
            plan_name=plan.name,
            monthly_recurring_revenue_usd=mrr,
            usage=self._usage.full_snapshot(firm_id),
            total_ai_cost_usd=total_ai_cost_usd,
            cache_hit_rate=self._cost_tracker.cache_hit_rate(firm_id),
            cache_savings_usd=cache_savings_usd,
            active_modules_count=len(self._modules.active_modules(firm_id)),
        )
