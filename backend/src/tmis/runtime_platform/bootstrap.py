from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.cloud_operations.bootstrap import (
    get_capacity_engine,
    get_circuit_breaker,
    get_metrics_engine,
    get_performance_engine,
    get_profiling_engine,
    get_workflow_monitoring_engine,
)
from tmis.core.config import get_settings
from tmis.platform.backup.bootstrap import get_backup_engine
from tmis.platform.disaster_recovery.bootstrap import get_disaster_recovery_engine
from tmis.platform.restore.bootstrap import get_restore_engine
from tmis.runtime_platform.async_processing.engine import AsyncProcessingEngine
from tmis.runtime_platform.async_processing.store import InMemoryAsyncJobStore
from tmis.runtime_platform.autoscaling_advisor.engine import AutoscalingAdvisorEngine
from tmis.runtime_platform.chaos_engineering.engine import RuntimeChaosEngine
from tmis.runtime_platform.cqrs.engine import CommandBus, QueryBus
from tmis.runtime_platform.disaster_recovery.engine import RuntimeDisasterRecoveryEngine
from tmis.runtime_platform.disaster_recovery.store import InMemoryBackupPolicyStore
from tmis.runtime_platform.distributed_cache.engine import DistributedCacheEngine
from tmis.runtime_platform.event_store.engine import EventStoreEngine
from tmis.runtime_platform.event_store.store import InMemoryEventStreamStore, InMemorySnapshotStore
from tmis.runtime_platform.event_streaming.engine import EventStreamingEngine
from tmis.runtime_platform.high_availability.engine import HighAvailabilityEngine
from tmis.runtime_platform.high_availability.store import InMemoryNodeHeartbeatStore
from tmis.runtime_platform.load_testing.engine import LoadTestingEngine
from tmis.runtime_platform.runtime_optimizer.engine import RuntimeOptimizerEngine
from tmis.runtime_platform.runtime_orchestrator.engine import RuntimeOrchestrator
from tmis.runtime_platform.runtime_orchestrator.store import InMemoryRuntimeTaskStore
from tmis.workflow_automation.bootstrap import get_workflow_event_bus


@lru_cache
def get_runtime_orchestrator() -> RuntimeOrchestrator:
    return RuntimeOrchestrator(InMemoryRuntimeTaskStore(), max_parallelism=4)


@lru_cache
def get_async_processing_engine() -> AsyncProcessingEngine:
    return AsyncProcessingEngine(InMemoryAsyncJobStore())


@lru_cache
def get_workflow_event_streaming_engine() -> EventStreamingEngine:
    """Decorates the existing `workflow_automation.event_bus.
    WorkflowEventBus` singleton — a new, additive way to publish
    workflow events with replay/idempotency/versioning/archival, on
    top of (not instead of) the bus's own subscriber dispatch. No
    existing publisher is required to switch; adoption is progressive
    like every other capability in this sprint."""
    return EventStreamingEngine(get_workflow_event_bus())


@lru_cache
def get_distributed_cache_engine() -> DistributedCacheEngine:
    return DistributedCacheEngine(get_kernel().cache)


@lru_cache
def get_event_store_engine() -> EventStoreEngine:
    return EventStoreEngine(InMemoryEventStreamStore(), InMemorySnapshotStore())


@lru_cache
def get_command_bus() -> CommandBus:
    return CommandBus()


@lru_cache
def get_query_bus() -> QueryBus:
    return QueryBus()


@lru_cache
def get_runtime_optimizer_engine() -> RuntimeOptimizerEngine:
    return RuntimeOptimizerEngine(
        get_metrics_engine(),
        get_performance_engine(),
        get_profiling_engine(),
        get_workflow_monitoring_engine(),
    )


@lru_cache
def get_high_availability_engine() -> HighAvailabilityEngine:
    return HighAvailabilityEngine(get_disaster_recovery_engine(), InMemoryNodeHeartbeatStore())


@lru_cache
def get_runtime_disaster_recovery_engine() -> RuntimeDisasterRecoveryEngine:
    return RuntimeDisasterRecoveryEngine(
        get_backup_engine(),
        get_restore_engine(),
        get_disaster_recovery_engine(),
        InMemoryBackupPolicyStore(),
    )


@lru_cache
def get_autoscaling_advisor_engine() -> AutoscalingAdvisorEngine:
    return AutoscalingAdvisorEngine(get_capacity_engine(), get_profiling_engine())


@lru_cache
def get_load_testing_engine() -> LoadTestingEngine:
    return LoadTestingEngine()


@lru_cache
def get_runtime_chaos_engine() -> RuntimeChaosEngine:
    """Shares the same `CircuitBreaker` singleton as
    `cloud_operations.chaos_testing.ChaosTestingEngine` — one
    resilience state per named dependency, never two."""
    return RuntimeChaosEngine(get_settings().environment, get_circuit_breaker())
