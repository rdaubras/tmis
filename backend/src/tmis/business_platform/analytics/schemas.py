from dataclasses import dataclass

from tmis.business_platform.plans.schemas import PlanName
from tmis.business_platform.usage.schemas import UsageSnapshot


@dataclass(frozen=True, slots=True)
class BusinessDashboard:
    """The commercial dashboard the sprint asks for — consumption, AI
    cost, usage breakdown, modules used, growth (`monthly_recurring_
    revenue_usd`, sourced from `pricing.PricingEngine`), savings
    (`cache_savings_usd`, derived from the cache-hit rate `ai_fabric.
    token_manager.TokenManager` already tracks — a cache hit costs
    nothing, so `cache_hit_rate * total_ai_calls` calls were free that
    would otherwise have been billed)."""

    firm_id: str
    plan_name: PlanName
    monthly_recurring_revenue_usd: float
    usage: list[UsageSnapshot]
    total_ai_cost_usd: float
    cache_hit_rate: float
    cache_savings_usd: float
    active_modules_count: int
