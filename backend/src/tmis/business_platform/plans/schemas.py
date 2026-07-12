from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class PlanName(StrEnum):
    """The five commercial tiers — "Trial, Basic, Professional,
    Business, Enterprise" (sprint requirement). Distinct from
    `cabinet_os.subscriptions.PlanTier` (Sprint 9: SOLO/CABINET/
    ENTERPRISE, still used by that module's own narrower
    plan+quota+usage engine) — same architectural role, richer and
    versioned catalog, documented not merged."""

    TRIAL = "trial"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True, slots=True)
class PlanLimits:
    """Per-plan limits — "limites, quotas... nombre d'utilisateurs,
    stockage, connecteurs disponibles" (sprint requirement)."""

    max_users: int
    max_storage_gb: float
    max_ai_calls_per_month: int
    max_cases: int
    max_workflows: int
    max_agents: int
    allowed_ai_models: frozenset[str] = frozenset()
    available_connectors: frozenset[str] = frozenset()


def new_plan_id(name: PlanName, version: int) -> str:
    return f"plan-{name.value}-v{version}"


@dataclass(frozen=True, slots=True)
class Plan:
    """One version of one commercial offer — "les plans sont
    versionnés" (sprint requirement). A new `Plan` version never
    mutates an existing one: a `Subscription` references the exact
    `plan_id` (name + version) it was sold under, so changing a plan's
    limits going forward never silently changes what an existing
    subscriber already agreed to."""

    id: str
    name: PlanName
    version: int
    limits: PlanLimits
    features: frozenset[str] = frozenset()
    monthly_price_usd: float = 0.0
    annual_price_usd: float = 0.0
    active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
