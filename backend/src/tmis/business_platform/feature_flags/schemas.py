from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from tmis.business_platform.plans.schemas import PlanName


class Environment(StrEnum):
    """Deployment environment a business flag extension may gate on —
    not covered by `platform.feature_flags.FeatureFlag`, which has no
    notion of environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass(slots=True)
class BusinessFlagExtras:
    """The four gating dimensions the sprint asks for that
    `platform.feature_flags.FeatureFlag` (kill switch, firm/user
    allow-list, plan allow-list, percentage rollout — Sprint 10) does
    not cover: environment, group, time window, experiment. Keyed by
    the same `key` as the base `FeatureFlag` it extends; a key with
    no `BusinessFlagExtras` behaves exactly as the base engine alone
    would evaluate it."""

    key: str
    enabled_environments: frozenset[Environment] = field(default_factory=frozenset)
    enabled_group_ids: frozenset[str] = field(default_factory=frozenset)
    enabled_plans: frozenset[PlanName] = field(default_factory=frozenset)
    window_start: datetime | None = None
    window_end: datetime | None = None
    experiment_key: str | None = None
    experiment_rollout_percentage: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.experiment_rollout_percentage <= 100.0:
            raise ValueError("experiment_rollout_percentage must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class BusinessFlagContext:
    """Extends `platform.feature_flags.FlagEvaluationContext` with the
    subject data the four extra gating dimensions need."""

    firm_id: str | None = None
    user_id: str | None = None
    plan_name: PlanName | None = None
    environment: Environment = Environment.PRODUCTION
    group_ids: frozenset[str] = frozenset()
    now: datetime | None = None
