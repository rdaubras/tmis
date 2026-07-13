from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException

from tmis.cloud_operations.bootstrap import get_metrics_engine
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.platform.autoscaling.schemas import AutoscalingPolicy
from tmis.runtime_platform.async_processing.engine import AsyncProcessingEngine
from tmis.runtime_platform.async_processing.schemas import AsyncJob, new_async_job_id
from tmis.runtime_platform.autoscaling_advisor.engine import AutoscalingAdvisorEngine
from tmis.runtime_platform.bootstrap import (
    get_async_processing_engine,
    get_autoscaling_advisor_engine,
    get_distributed_cache_engine,
    get_event_store_engine,
    get_high_availability_engine,
    get_load_testing_engine,
    get_runtime_chaos_engine,
    get_runtime_disaster_recovery_engine,
    get_runtime_optimizer_engine,
    get_runtime_orchestrator,
    get_workflow_event_streaming_engine,
)
from tmis.runtime_platform.chaos_engineering.engine import RuntimeChaosEngine
from tmis.runtime_platform.chaos_engineering.schemas import RuntimeChaosScenarioType
from tmis.runtime_platform.disaster_recovery.engine import RuntimeDisasterRecoveryEngine
from tmis.runtime_platform.distributed_cache.engine import DistributedCacheEngine
from tmis.runtime_platform.event_store.engine import ArchivedStreamError, EventStoreEngine
from tmis.runtime_platform.event_streaming.engine import EventStreamingEngine
from tmis.runtime_platform.high_availability.engine import HighAvailabilityEngine
from tmis.runtime_platform.load_testing.engine import LoadTestingEngine
from tmis.runtime_platform.load_testing.schemas import LoadTestPreset
from tmis.runtime_platform.runtime_optimizer.engine import RuntimeOptimizerEngine
from tmis.runtime_platform.runtime_orchestrator.engine import RuntimeOrchestrator
from tmis.runtime_platform.runtime_orchestrator.schemas import RuntimeTask

router = APIRouter(prefix="/runtime", tags=["runtime-platform"])
"""Deliberately outside `/api/v1`, unauthenticated — same "operational
concern, not a versioned business API" precedent as
`cloud_operations.api.routes` and `platform.api.routes` (see
`main.py`). `runtime_orchestrator.run`/`.resume` are intentionally
*not* exposed here: they take a Python coroutine as their runner,
which has no meaningful REST representation — see
docs/runtime-platform guides and the Sprint 23 demo report for how a
caller drives them from Python (e.g. reusing the Workflow Engine via
`workflow_execution_task_runner`)."""


# ---------------------------------------------------------------------------
# Runtime Orchestrator
# ---------------------------------------------------------------------------


@router.post("/tasks")
def submit_task(
    task_id: str,
    name: str,
    priority: int = 0,
    depends_on: list[str] | None = None,
    firm_id: str | None = None,
    orchestrator: RuntimeOrchestrator = Depends(get_runtime_orchestrator),
) -> dict[str, object]:
    task = RuntimeTask(
        id=task_id,
        name=name,
        priority=priority,
        depends_on=frozenset(depends_on or []),
        firm_id=firm_id,
    )
    orchestrator.submit(task)
    return _task_payload(task)


@router.get("/tasks")
def list_tasks(
    orchestrator: RuntimeOrchestrator = Depends(get_runtime_orchestrator),
) -> list[dict[str, object]]:
    return [_task_payload(t) for t in orchestrator.all()]


@router.get("/tasks/ready")
def ready_tasks(
    orchestrator: RuntimeOrchestrator = Depends(get_runtime_orchestrator),
) -> list[dict[str, object]]:
    return [_task_payload(t) for t in orchestrator.ready_tasks()]


@router.post("/tasks/{task_id}/cancel")
def cancel_task(
    task_id: str, orchestrator: RuntimeOrchestrator = Depends(get_runtime_orchestrator)
) -> dict[str, bool]:
    return {"cancelled": orchestrator.cancel(task_id)}


def _task_payload(task: RuntimeTask) -> dict[str, object]:
    return {
        "id": task.id,
        "name": task.name,
        "priority": task.priority,
        "depends_on": sorted(task.depends_on),
        "status": task.status.value,
        "checkpoint": task.checkpoint,
        "firm_id": task.firm_id,
    }


# ---------------------------------------------------------------------------
# Async Processing
# ---------------------------------------------------------------------------


@router.post("/jobs")
def enqueue_job(
    queue_name: str,
    priority: int = 0,
    max_attempts: int = 3,
    timeout_seconds: float = 30.0,
    delay_seconds: float = 0.0,
    engine: AsyncProcessingEngine = Depends(get_async_processing_engine),
    metrics: MetricsEngine = Depends(get_metrics_engine),
) -> dict[str, object]:
    job = AsyncJob(
        id=new_async_job_id(),
        queue_name=queue_name,
        priority=priority,
        max_attempts=max_attempts,
        timeout_seconds=timeout_seconds,
    )
    engine.enqueue(job, delay_seconds=delay_seconds)
    metrics.record(MetricCategory.QUEUE_DEPTH, "runtime.async_processing.jobs", 1.0)
    return _job_payload(job)


@router.post("/jobs/{job_id}/fail")
def fail_job(
    job_id: str, error: str, engine: AsyncProcessingEngine = Depends(get_async_processing_engine)
) -> dict[str, object]:
    try:
        job = engine.mark_failed(job_id, error)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="job not found") from exc
    return _job_payload(job)


@router.get("/jobs/dead-letters")
def dead_letter_jobs(
    queue_name: str | None = None,
    engine: AsyncProcessingEngine = Depends(get_async_processing_engine),
) -> list[dict[str, object]]:
    return [_job_payload(j) for j in engine.dead_letters(queue_name=queue_name)]


def _job_payload(job: AsyncJob) -> dict[str, object]:
    return {
        "id": job.id,
        "queue_name": job.queue_name,
        "priority": job.priority,
        "status": job.status.value,
        "attempts": job.attempts,
        "max_attempts": job.max_attempts,
        "run_at": job.run_at.isoformat() if job.run_at else None,
        "dead_letter_reason": job.dead_letter_reason,
    }


# ---------------------------------------------------------------------------
# Event Streaming (workflow bus)
# ---------------------------------------------------------------------------


@router.get("/events/workflow/replay")
def replay_workflow_events(
    from_sequence: int = 0,
    engine: EventStreamingEngine = Depends(get_workflow_event_streaming_engine),
) -> list[dict[str, object]]:
    return [
        {
            "sequence": e.sequence,
            "event_type": e.event_type,
            "version": e.version,
            "recorded_at": e.recorded_at.isoformat(),
        }
        for e in engine.replay(from_sequence)
    ]


@router.post("/events/workflow/archive")
def archive_workflow_events(
    before_sequence: int,
    engine: EventStreamingEngine = Depends(get_workflow_event_streaming_engine),
) -> dict[str, int]:
    return {"archived_count": engine.archive(before_sequence)}


# ---------------------------------------------------------------------------
# Distributed Cache
# ---------------------------------------------------------------------------


@router.get("/cache/stats")
def cache_stats(
    engine: DistributedCacheEngine = Depends(get_distributed_cache_engine),
    metrics: MetricsEngine = Depends(get_metrics_engine),
) -> dict[str, object]:
    stats = engine.stats
    metrics.record(MetricCategory.CACHE, "runtime.cache.hits", float(stats.hits))
    metrics.record(MetricCategory.CACHE, "runtime.cache.misses", float(stats.misses))
    return {
        "hits": stats.hits,
        "misses": stats.misses,
        "sets": stats.sets,
        "invalidations": stats.invalidations,
        "warmed_keys": stats.warmed_keys,
        "bytes_saved_by_compression": stats.bytes_saved_by_compression,
    }


# ---------------------------------------------------------------------------
# Event Store
# ---------------------------------------------------------------------------


@router.post("/event-store/{stream_id}/events")
def append_event(
    stream_id: str,
    event_type: str,
    payload: dict[str, object],
    engine: EventStoreEngine = Depends(get_event_store_engine),
) -> dict[str, object]:
    try:
        event = engine.append(stream_id, event_type, payload)
    except ArchivedStreamError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "stream_id": event.stream_id,
        "sequence": event.sequence,
        "event_type": event.event_type,
        "recorded_at": event.recorded_at.isoformat(),
    }


@router.get("/event-store/{stream_id}/replay")
def replay_stream(
    stream_id: str, engine: EventStoreEngine = Depends(get_event_store_engine)
) -> list[dict[str, object]]:
    return [
        {
            "sequence": e.sequence,
            "event_type": e.event_type,
            "payload": e.payload,
            "recorded_at": e.recorded_at.isoformat(),
        }
        for e in engine.replay(stream_id)
    ]


@router.post("/event-store/{stream_id}/snapshot")
def snapshot_stream(
    stream_id: str,
    state: dict[str, object],
    engine: EventStoreEngine = Depends(get_event_store_engine),
) -> dict[str, object]:
    snapshot = engine.snapshot(stream_id, state)
    return {"stream_id": snapshot.stream_id, "version": snapshot.version}


@router.post("/event-store/{stream_id}/archive")
def archive_stream(
    stream_id: str, engine: EventStoreEngine = Depends(get_event_store_engine)
) -> dict[str, bool]:
    engine.archive(stream_id)
    return {"archived": True}


@router.post("/event-store/{stream_id}/restore")
def restore_stream(
    stream_id: str, engine: EventStoreEngine = Depends(get_event_store_engine)
) -> dict[str, bool]:
    engine.restore(stream_id)
    return {"archived": False}


# ---------------------------------------------------------------------------
# Runtime Optimizer
# ---------------------------------------------------------------------------


@router.get("/optimizer/recommendations")
def optimizer_recommendations(
    firm_id: str | None = None,
    engine: RuntimeOptimizerEngine = Depends(get_runtime_optimizer_engine),
) -> list[dict[str, object]]:
    return [
        {
            "category": r.category.value,
            "severity": r.severity.value,
            "metric_value": r.metric_value,
            "description": r.description,
        }
        for r in engine.analyze(firm_id)
    ]


# ---------------------------------------------------------------------------
# High Availability
# ---------------------------------------------------------------------------


@router.post("/ha/heartbeat/{node_id}")
def send_heartbeat(
    node_id: str, engine: HighAvailabilityEngine = Depends(get_high_availability_engine)
) -> dict[str, str]:
    engine.heartbeat(node_id)
    return {"node_id": node_id, "status": engine.node_status(node_id).value}


@router.get("/ha/supervise")
def supervise_nodes(
    engine: HighAvailabilityEngine = Depends(get_high_availability_engine),
) -> dict[str, str]:
    return {node_id: status.value for node_id, status in engine.supervise().items()}


@router.get("/ha/failover/{node_id}")
def failover_decision(
    node_id: str,
    engine: HighAvailabilityEngine = Depends(get_high_availability_engine),
    metrics: MetricsEngine = Depends(get_metrics_engine),
) -> dict[str, object]:
    decision = engine.decide_failover(node_id)
    metrics.record(
        MetricCategory.ERRORS,
        "runtime.ha.failover_declared",
        1.0 if decision.should_failover else 0.0,
    )
    return {"should_failover": decision.should_failover, "reason": decision.reason}


# ---------------------------------------------------------------------------
# Disaster Recovery
# ---------------------------------------------------------------------------


@router.post("/disaster-recovery/policy/{firm_id}")
def set_backup_policy(
    firm_id: str,
    schedule_cron: str,
    retention_days: int,
    engine: RuntimeDisasterRecoveryEngine = Depends(get_runtime_disaster_recovery_engine),
) -> dict[str, object]:
    policy = engine.set_policy(firm_id, schedule_cron, retention_days)
    return {
        "firm_id": policy.firm_id,
        "schedule_cron": policy.schedule_cron,
        "retention_days": policy.retention_days,
    }


@router.get("/disaster-recovery/simulate-restore/{backup_id}")
def simulate_restore(
    backup_id: str,
    engine: RuntimeDisasterRecoveryEngine = Depends(get_runtime_disaster_recovery_engine),
) -> dict[str, object]:
    try:
        result = engine.simulate_restore(backup_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "backup_id": result.backup_id,
        "files": result.plan.files,
        "total_size_bytes": result.plan.total_size_bytes,
        "integrity_valid": result.integrity_valid,
    }


@router.get("/disaster-recovery/rpo-rto")
def rpo_rto_estimate(
    last_backup_at: str | None = None,
    engine: RuntimeDisasterRecoveryEngine = Depends(get_runtime_disaster_recovery_engine),
) -> dict[str, object]:
    parsed = datetime.fromisoformat(last_backup_at).astimezone(UTC) if last_backup_at else None
    estimate = engine.estimate_rpo_rto(parsed)
    return {
        "rto_minutes": estimate.rto_minutes,
        "rpo_minutes": estimate.rpo_minutes,
        "actual_rpo_minutes": estimate.actual_rpo_minutes,
        "meets_objective": estimate.meets_objective,
    }


# ---------------------------------------------------------------------------
# Autoscaling Advisor
# ---------------------------------------------------------------------------


@router.get("/autoscaling/recommend/{category}")
def autoscaling_recommendation(
    category: MetricCategory,
    current_replicas: int,
    min_replicas: int = 1,
    max_replicas: int = 10,
    target_cpu_percent: int = 70,
    target_memory_percent: int = 75,
    firm_id: str | None = None,
    periods_ahead: int = 1,
    engine: AutoscalingAdvisorEngine = Depends(get_autoscaling_advisor_engine),
) -> dict[str, object] | None:
    policy = AutoscalingPolicy(
        min_replicas=min_replicas,
        max_replicas=max_replicas,
        target_cpu_percent=target_cpu_percent,
        target_memory_percent=target_memory_percent,
    )
    recommendation = engine.recommend(
        category, policy, current_replicas, firm_id=firm_id, periods_ahead=periods_ahead
    )
    if recommendation is None:
        return None
    return {
        "category": recommendation.category.value,
        "current_replicas": recommendation.current_replicas,
        "recommended_replicas": recommendation.recommended_replicas,
        "growth_rate_percent": recommendation.growth_rate_percent,
        "reason": recommendation.reason,
    }


@router.get("/autoscaling/bottlenecks")
def autoscaling_bottlenecks(
    limit: int = 5, engine: AutoscalingAdvisorEngine = Depends(get_autoscaling_advisor_engine)
) -> list[dict[str, object]]:
    return [
        {
            "finding_type": b.finding_type.value,
            "name": b.name,
            "average_duration_ms": b.average_duration_ms,
            "occurrence_count": b.occurrence_count,
            "recommendation": b.recommendation,
        }
        for b in engine.bottlenecks(limit)
    ]


# ---------------------------------------------------------------------------
# Load Testing
# ---------------------------------------------------------------------------


@router.post("/load-test/{preset}")
async def run_load_test(
    preset: LoadTestPreset, engine: LoadTestingEngine = Depends(get_load_testing_engine)
) -> dict[str, object]:
    """Runs the in-process virtual-user simulation described in
    docs/runtime-platform guides against a synthetic no-op target —
    this measures the harness itself, not a real business endpoint;
    a caller driving this from Python can pass any real coroutine as
    `target` instead (see the Sprint 23 demo report)."""

    async def _noop() -> None:
        return None

    report = await engine.run(preset, _noop)
    return {
        "concurrent_users": report.concurrent_users,
        "total_requests": report.total_requests,
        "success_count": report.success_count,
        "error_count": report.error_count,
        "avg_latency_ms": report.avg_latency_ms,
        "p95_latency_ms": report.p95_latency_ms,
        "throughput_rps": report.throughput_rps,
        "duration_seconds": report.duration_seconds,
    }


# ---------------------------------------------------------------------------
# Chaos Engineering
# ---------------------------------------------------------------------------


@router.post("/chaos/{scenario}")
def run_chaos_scenario(
    scenario: RuntimeChaosScenarioType,
    authorized: bool = False,
    engine: RuntimeChaosEngine = Depends(get_runtime_chaos_engine),
) -> dict[str, object]:
    from tmis.cloud_operations.chaos_testing.engine import ProductionChaosTestingForbiddenError

    try:
        result = engine.run_scenario(scenario, authorized=authorized)
    except ProductionChaosTestingForbiddenError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {"scenario": result.scenario.value, "dependency": result.dependency}


@router.post("/chaos/{scenario}/probe")
def probe_chaos_scenario(
    scenario: RuntimeChaosScenarioType,
    engine: RuntimeChaosEngine = Depends(get_runtime_chaos_engine),
) -> dict[str, bool]:
    try:
        return {"available": engine.probe(scenario)}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/chaos/{scenario}/recover")
def recover_chaos_scenario(
    scenario: RuntimeChaosScenarioType,
    item_loss_count: int = 0,
    engine: RuntimeChaosEngine = Depends(get_runtime_chaos_engine),
    metrics: MetricsEngine = Depends(get_metrics_engine),
) -> dict[str, object]:
    try:
        result = engine.measure_recovery(scenario, item_loss_count=item_loss_count)
    except (KeyError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    metrics.record(
        MetricCategory.ERRORS,
        f"runtime.chaos.{scenario.value}.recovery_time_seconds",
        result.recovery_time_seconds or 0.0,
    )
    return {
        "scenario": result.scenario.value,
        "recovery_time_seconds": result.recovery_time_seconds,
        "availability_ratio": result.availability_ratio,
        "item_loss_count": result.item_loss_count,
    }
