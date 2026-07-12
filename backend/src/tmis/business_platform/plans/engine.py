from tmis.business_platform.plans.ports import PlanStorePort
from tmis.business_platform.plans.schemas import Plan, PlanLimits, PlanName, new_plan_id


class PlanCatalog:
    """Registers and resolves versioned commercial plans. Publishing a
    new version of a plan never mutates the previous one — existing
    subscriptions keep referencing the exact `plan_id` they were sold
    under (see `subscriptions.engine.SubscriptionEngine`)."""

    def __init__(self, store: PlanStorePort) -> None:
        self._store = store

    def publish(
        self,
        name: PlanName,
        limits: PlanLimits,
        *,
        features: frozenset[str] = frozenset(),
        monthly_price_usd: float = 0.0,
        annual_price_usd: float = 0.0,
    ) -> Plan:
        existing_versions = self._store.list_versions(name)
        next_version = (existing_versions[-1].version + 1) if existing_versions else 1
        plan = Plan(
            id=new_plan_id(name, next_version),
            name=name,
            version=next_version,
            limits=limits,
            features=features,
            monthly_price_usd=monthly_price_usd,
            annual_price_usd=annual_price_usd,
        )
        self._store.save(plan)
        return plan

    def get(self, plan_id: str) -> Plan:
        plan = self._store.get(plan_id)
        if plan is None:
            raise KeyError(plan_id)
        return plan

    def latest(self, name: PlanName) -> Plan:
        versions = self._store.list_versions(name)
        if not versions:
            raise KeyError(name)
        return versions[-1]

    def list_versions(self, name: PlanName) -> list[Plan]:
        return self._store.list_versions(name)

    def list_current_catalog(self) -> list[Plan]:
        return self._store.list_latest()

    def deactivate(self, plan_id: str) -> Plan:
        plan = self.get(plan_id)
        updated = Plan(
            id=plan.id,
            name=plan.name,
            version=plan.version,
            limits=plan.limits,
            features=plan.features,
            monthly_price_usd=plan.monthly_price_usd,
            annual_price_usd=plan.annual_price_usd,
            active=False,
            created_at=plan.created_at,
        )
        self._store.save(updated)
        return updated


_DEFAULT_LIMITS: dict[PlanName, PlanLimits] = {
    PlanName.TRIAL: PlanLimits(
        max_users=3,
        max_storage_gb=5.0,
        max_ai_calls_per_month=200,
        max_cases=10,
        max_workflows=5,
        max_agents=2,
        allowed_ai_models=frozenset({"gpt-4o-mini"}),
    ),
    PlanName.BASIC: PlanLimits(
        max_users=5,
        max_storage_gb=20.0,
        max_ai_calls_per_month=1_000,
        max_cases=50,
        max_workflows=20,
        max_agents=3,
        allowed_ai_models=frozenset({"gpt-4o-mini"}),
    ),
    PlanName.PROFESSIONAL: PlanLimits(
        max_users=25,
        max_storage_gb=100.0,
        max_ai_calls_per_month=10_000,
        max_cases=500,
        max_workflows=100,
        max_agents=8,
        allowed_ai_models=frozenset({"gpt-4o-mini", "gpt-4o", "claude-sonnet"}),
        available_connectors=frozenset({"calendar", "messaging", "billing"}),
    ),
    PlanName.BUSINESS: PlanLimits(
        max_users=100,
        max_storage_gb=500.0,
        max_ai_calls_per_month=50_000,
        max_cases=5_000,
        max_workflows=500,
        max_agents=20,
        allowed_ai_models=frozenset({"gpt-4o-mini", "gpt-4o", "claude-sonnet", "claude-opus"}),
        available_connectors=frozenset(
            {"calendar", "messaging", "billing", "crm", "document_storage", "esignature"}
        ),
    ),
    PlanName.ENTERPRISE: PlanLimits(
        max_users=10_000,
        max_storage_gb=10_000.0,
        max_ai_calls_per_month=1_000_000,
        max_cases=1_000_000,
        max_workflows=100_000,
        max_agents=1_000,
        allowed_ai_models=frozenset(
            {"gpt-4o-mini", "gpt-4o", "claude-sonnet", "claude-opus", "claude-fable"}
        ),
        available_connectors=frozenset(
            {"calendar", "messaging", "billing", "crm", "document_storage", "esignature", "dms"}
        ),
    ),
}

_DEFAULT_FEATURES: dict[PlanName, frozenset[str]] = {
    PlanName.TRIAL: frozenset({"cases", "documents", "ai_assist"}),
    PlanName.BASIC: frozenset({"cases", "documents", "ai_assist"}),
    PlanName.PROFESSIONAL: frozenset(
        {"cases", "documents", "ai_assist", "collaboration", "billing", "workflow_automation"}
    ),
    PlanName.BUSINESS: frozenset(
        {
            "cases",
            "documents",
            "ai_assist",
            "collaboration",
            "billing",
            "workflow_automation",
            "integration_hub",
            "advanced_analytics",
        }
    ),
    PlanName.ENTERPRISE: frozenset(
        {
            "cases",
            "documents",
            "ai_assist",
            "collaboration",
            "billing",
            "workflow_automation",
            "integration_hub",
            "advanced_analytics",
            "sso",
            "audit_export",
            "public_api",
        }
    ),
}

_DEFAULT_MONTHLY_PRICE_USD: dict[PlanName, float] = {
    PlanName.TRIAL: 0.0,
    PlanName.BASIC: 49.0,
    PlanName.PROFESSIONAL: 199.0,
    PlanName.BUSINESS: 599.0,
    PlanName.ENTERPRISE: 1_999.0,
}


def seed_default_catalog(catalog: PlanCatalog) -> list[Plan]:
    """Publishes version 1 of each of the five default plans — a
    reasonable starting catalog a firm can subscribe against
    immediately; a real deployment would adjust pricing/limits via
    `PlanCatalog.publish` (a new version) rather than editing these
    defaults in place."""
    return [
        catalog.publish(
            name,
            _DEFAULT_LIMITS[name],
            features=_DEFAULT_FEATURES[name],
            monthly_price_usd=_DEFAULT_MONTHLY_PRICE_USD[name],
            annual_price_usd=_DEFAULT_MONTHLY_PRICE_USD[name] * 10,
        )
        for name in PlanName
    ]
