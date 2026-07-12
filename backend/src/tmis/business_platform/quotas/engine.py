from tmis.ai_fabric.quotas.engine import QuotaEngine as AiFabricQuotaEngine
from tmis.business_platform.plans.engine import PlanCatalog
from tmis.business_platform.plans.schemas import PlanLimits
from tmis.business_platform.quotas.ports import QuotaOverrideStorePort
from tmis.business_platform.quotas.schemas import QuotaCheckResult, QuotaDimension, QuotaOverride
from tmis.business_platform.subscriptions.engine import SubscriptionEngine

_BASE_LIMIT_FIELD: dict[QuotaDimension, str] = {
    QuotaDimension.USERS: "max_users",
    QuotaDimension.STORAGE_GB: "max_storage_gb",
    QuotaDimension.AI_CALLS: "max_ai_calls_per_month",
    QuotaDimension.CASES: "max_cases",
    QuotaDimension.WORKFLOWS: "max_workflows",
    QuotaDimension.AGENTS: "max_agents",
}


def _base_limit(limits: PlanLimits, dimension: QuotaDimension) -> int:
    """GPU time has no plan-level allowance — see
    `QuotaDimension.GPU_MINUTES` docstring: it is only ever granted
    through a `QuotaOverride` (an add-on option), so its base is
    always zero."""
    field = _BASE_LIMIT_FIELD.get(dimension)
    if field is None:
        return 0
    return int(getattr(limits, field))


class BusinessQuotaEngine:
    """Multi-dimension quota gate for the SaaS Business Platform —
    "utilisateurs, stockage, appels IA, temps GPU, dossiers,
    workflows, agents" (sprint requirement), each resolved from the
    firm's current plan plus any `QuotaOverride` bought as an option.
    Composes `ai_fabric.quotas.QuotaEngine` directly for the AI-call
    dimension specifically (Sprint 14's own generic scope-based hard
    gate) rather than reimplementing call-rate gating."""

    def __init__(
        self,
        plans: PlanCatalog,
        subscriptions: SubscriptionEngine,
        overrides: QuotaOverrideStorePort,
        ai_fabric_quotas: AiFabricQuotaEngine,
    ) -> None:
        self._plans = plans
        self._subscriptions = subscriptions
        self._overrides = overrides
        self._ai_fabric_quotas = ai_fabric_quotas

    def limit_for(self, firm_id: str, dimension: QuotaDimension) -> int:
        subscription = self._subscriptions.get(firm_id)
        plan = self._plans.get(subscription.plan_id)
        base = _base_limit(plan.limits, dimension)
        override = self._overrides.get(firm_id, dimension)
        return base + (override.extra_amount if override is not None else 0)

    def set_override(
        self, firm_id: str, dimension: QuotaDimension, extra_amount: int
    ) -> QuotaOverride:
        override = QuotaOverride(firm_id=firm_id, dimension=dimension, extra_amount=extra_amount)
        self._overrides.save(override)
        return override

    def check(
        self, firm_id: str, dimension: QuotaDimension, current_usage: int
    ) -> QuotaCheckResult:
        limit = self.limit_for(firm_id, dimension)
        return QuotaCheckResult(
            dimension=dimension, limit=limit, used=current_usage, allowed=current_usage < limit
        )

    def check_ai_calls(self, firm_id: str) -> bool:
        limit = self.limit_for(firm_id, QuotaDimension.AI_CALLS)
        self._ai_fabric_quotas.set_quota("firm", firm_id, limit, period_days=30)
        return self._ai_fabric_quotas.check("firm", firm_id)

    def record_ai_call(self, firm_id: str) -> None:
        self._ai_fabric_quotas.record_call("firm", firm_id)
