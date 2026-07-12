from tmis.cloud_operations.capacity.engine import CapacityEngine
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.cloud_operations.profiling.engine import ProfilingEngine
from tmis.cloud_operations.profiling.schemas import ProfilingFindingType
from tmis.cloud_operations.profiling.store import InMemoryProfilingSampleStore
from tmis.platform.autoscaling.schemas import AutoscalingPolicy
from tmis.platform.metrics.registry import MetricsRegistry
from tmis.runtime_platform.autoscaling_advisor.engine import AutoscalingAdvisorEngine


def _engine() -> tuple[AutoscalingAdvisorEngine, MetricsEngine, ProfilingEngine]:
    metrics = MetricsEngine(InMemoryMetricEventStore(), MetricsRegistry())
    capacity = CapacityEngine(metrics)
    profiling = ProfilingEngine(InMemoryProfilingSampleStore())
    return AutoscalingAdvisorEngine(capacity, profiling), metrics, profiling


def test_recommend_returns_none_without_enough_history() -> None:
    engine, _, _ = _engine()
    policy = AutoscalingPolicy(
        min_replicas=1, max_replicas=5, target_cpu_percent=70, target_memory_percent=75
    )
    assert engine.recommend(MetricCategory.QUEUE_DEPTH, policy, current_replicas=2) is None


def test_recommend_scales_up_on_growth_and_respects_max() -> None:
    engine, metrics, _ = _engine()
    for value in (10, 15, 20, 25, 30, 100):
        metrics.record(MetricCategory.QUEUE_DEPTH, "sync-queue", value)
    policy = AutoscalingPolicy(
        min_replicas=1, max_replicas=3, target_cpu_percent=70, target_memory_percent=75
    )

    recommendation = engine.recommend(MetricCategory.QUEUE_DEPTH, policy, current_replicas=2)
    assert recommendation is not None
    assert recommendation.recommended_replicas <= 3
    assert recommendation.growth_rate_percent > 0


def test_recommend_does_not_scale_up_when_flat_or_shrinking() -> None:
    engine, metrics, _ = _engine()
    for value in (30, 25, 20, 15, 10, 5):
        metrics.record(MetricCategory.QUEUE_DEPTH, "sync-queue", value)
    policy = AutoscalingPolicy(
        min_replicas=1, max_replicas=5, target_cpu_percent=70, target_memory_percent=75
    )

    recommendation = engine.recommend(MetricCategory.QUEUE_DEPTH, policy, current_replicas=2)
    assert recommendation is not None
    assert recommendation.recommended_replicas == 2


def test_bottlenecks_aggregates_across_finding_types() -> None:
    engine, _metrics, profiling = _engine()
    profiling.record(ProfilingFindingType.SLOW_FUNCTION, "slow_fn", 400.0)
    profiling.record(ProfilingFindingType.COSTLY_QUERY, "big_query", 900.0)

    bottlenecks = engine.bottlenecks(limit=5)
    assert bottlenecks[0].name == "big_query"
    assert {b.name for b in bottlenecks} == {"slow_fn", "big_query"}
