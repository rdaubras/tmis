from dataclasses import dataclass, field

from tmis.cabinet_os.subscriptions.schemas import PlanTier


@dataclass(slots=True)
class FeatureFlag:
    """A single togglable feature (see docs/47-guide-securite-entreprise.md
    — Feature Flags). Evaluation order in `FeatureFlagEngine.is_enabled`:
    kill switch -> explicit firm/user allow-list -> plan allow-list ->
    percentage rollout. `rollout_percentage` drives a deterministic,
    stable bucketing (same firm/user always lands on the same side of
    the threshold for a given `key`) so a progressive rollout never
    flickers a subject in and out."""

    key: str
    description: str = ""
    enabled: bool = True
    enabled_firm_ids: frozenset[str] = frozenset()
    enabled_user_ids: frozenset[str] = frozenset()
    enabled_plans: frozenset[PlanTier] = frozenset()
    rollout_percentage: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.rollout_percentage <= 100.0:
            raise ValueError("rollout_percentage must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class FlagEvaluationContext:
    firm_id: str | None = None
    user_id: str | None = None
    plan: PlanTier | None = None
