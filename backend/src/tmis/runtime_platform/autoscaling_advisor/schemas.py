from dataclasses import dataclass

from tmis.cloud_operations.metrics.schemas import MetricCategory


@dataclass(frozen=True, slots=True)
class ScalingRecommendation:
    """Cloud-provider-independent: a replica count and a reason,
    never a call to any cloud SDK. `platform.autoscaling.
    AutoscalingPolicy` (Sprint 10) already models the min/max/target
    bounds a Kubernetes HPA would enforce; this recommendation stays
    within those bounds rather than inventing a second policy
    concept."""

    category: MetricCategory
    current_replicas: int
    recommended_replicas: int
    growth_rate_percent: float
    reason: str
