import math

from tmis.cloud_operations.capacity.engine import CapacityEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.profiling.engine import ProfilingEngine
from tmis.cloud_operations.profiling.schemas import ProfilingFindingType, ProfilingRecommendation
from tmis.platform.autoscaling.schemas import AutoscalingPolicy
from tmis.runtime_platform.autoscaling_advisor.schemas import ScalingRecommendation


class AutoscalingAdvisorEngine:
    """Composes `cloud_operations.capacity.CapacityEngine` (growth
    projection) and `cloud_operations.profiling.ProfilingEngine`
    (bottleneck detection) — both already existing and confirmed by
    the Sprint 23 Phase 1 audit to compute real, working numbers off
    `cloud_operations.metrics` history — into scale-up
    recommendations bounded by an existing `platform.autoscaling.
    AutoscalingPolicy`. Produces a replica count and a reason, never
    a cloud API call, so it stays usable regardless of which
    orchestrator (Kubernetes, ECS, or none yet) ultimately acts on
    it."""

    def __init__(self, capacity: CapacityEngine, profiling: ProfilingEngine) -> None:
        self._capacity = capacity
        self._profiling = profiling

    def recommend(
        self,
        category: MetricCategory,
        policy: AutoscalingPolicy,
        current_replicas: int,
        *,
        firm_id: str | None = None,
        periods_ahead: int = 1,
    ) -> ScalingRecommendation | None:
        forecast = self._capacity.forecast(category, firm_id, periods_ahead=periods_ahead)
        if forecast is None:
            return None
        if forecast.growth_rate_percent <= 0:
            target = current_replicas
            reason = f"{category.value} is flat or shrinking — no scale-up needed."
        else:
            target = math.ceil(current_replicas * (1 + forecast.growth_rate_percent / 100))
            reason = (
                f"Projected {category.value} growth of "
                f"{forecast.growth_rate_percent:.1f}% over the next "
                f"{periods_ahead} period(s)."
            )
        recommended = min(max(target, policy.min_replicas), policy.max_replicas)
        return ScalingRecommendation(
            category=category,
            current_replicas=current_replicas,
            recommended_replicas=recommended,
            growth_rate_percent=forecast.growth_rate_percent,
            reason=reason,
        )

    def bottlenecks(self, limit: int = 5) -> list[ProfilingRecommendation]:
        findings = [
            recommendation
            for finding_type in ProfilingFindingType
            for recommendation in self._profiling.top_offenders(finding_type, limit=limit)
        ]
        findings.sort(key=lambda r: r.average_duration_ms, reverse=True)
        return findings[:limit]
