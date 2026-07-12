from functools import lru_cache

from tmis.ai_fabric.bootstrap import get_fallback_engine, get_model_registry, get_quality_optimizer
from tmis.business_platform.bootstrap import get_analytics_engine, get_subscription_engine
from tmis.cloud_operations.alerting.engine import AlertingEngine
from tmis.cloud_operations.alerting.store import InMemoryAlertEventStore, InMemoryAlertRuleStore
from tmis.cloud_operations.cache.engine import CacheObservabilityEngine
from tmis.cloud_operations.capacity.engine import CapacityEngine
from tmis.cloud_operations.chaos_testing.engine import ChaosTestingEngine
from tmis.cloud_operations.dashboards.engine import DashboardsEngine
from tmis.cloud_operations.diagnostics.engine import DiagnosticsEngine
from tmis.cloud_operations.error_tracking.engine import ErrorTrackingEngine
from tmis.cloud_operations.error_tracking.store import InMemoryErrorEventStore
from tmis.cloud_operations.health_checks.engine import register_business_context_health_checks
from tmis.cloud_operations.incident_management.engine import IncidentManagementEngine
from tmis.cloud_operations.incident_management.store import (
    InMemoryIncidentStore,
    InMemoryIncidentUpdateStore,
)
from tmis.cloud_operations.logging.engine import LoggingGovernanceEngine
from tmis.cloud_operations.logging.store import InMemoryLogRetentionPolicyStore
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.store import InMemoryMetricEventStore
from tmis.cloud_operations.performance.engine import PerformanceEngine
from tmis.cloud_operations.profiling.engine import ProfilingEngine
from tmis.cloud_operations.profiling.store import InMemoryProfilingSampleStore
from tmis.cloud_operations.queue_monitoring.engine import QueueObservabilityEngine
from tmis.cloud_operations.resilience.engine import CircuitBreaker
from tmis.cloud_operations.runbooks.engine import RunbooksEngine
from tmis.cloud_operations.sla.engine import SLAEngine
from tmis.cloud_operations.sla.store import InMemorySLASampleStore, InMemorySLATargetStore
from tmis.cloud_operations.slo.engine import SLOEngine
from tmis.cloud_operations.slo.store import InMemorySLOTargetStore
from tmis.cloud_operations.telemetry.engine import TelemetryEngine
from tmis.cloud_operations.telemetry.store import InMemoryTelemetryEventStore
from tmis.cloud_operations.tracing.engine import TracingEngine
from tmis.cloud_operations.tracing.store import InMemorySpanStore
from tmis.collaboration.bootstrap import get_notification_engine
from tmis.core.config import get_settings
from tmis.identity_platform.bootstrap import (
    get_authorization_engine,
    get_identity_monitoring_engine,
)
from tmis.integration_hub.bootstrap import get_connector_registry_engine
from tmis.platform.cost_control.bootstrap import get_cost_tracker_engine
from tmis.platform.health.bootstrap import get_health_check_engine
from tmis.platform.health.engine import HealthCheckEngine
from tmis.platform.metrics.bootstrap import get_metrics_registry
from tmis.platform.monitoring.bootstrap import get_monitoring_engine
from tmis.platform_sdk.bootstrap import get_plugin_registry
from tmis.workflow_automation.bootstrap import get_workflow_engine


@lru_cache
def get_metrics_engine() -> MetricsEngine:
    """Process-wide composition root for `tmis.cloud_operations` — the
    Cloud Operations & Observability Platform (see
    docs/125-architecture-cloud-operations.md). Composes `platform.
    metrics.MetricsRegistry` (Sprint 10), the shared Prometheus
    registry, rather than a second one."""
    return MetricsEngine(InMemoryMetricEventStore(), get_metrics_registry())


@lru_cache
def get_logging_governance_engine() -> LoggingGovernanceEngine:
    return LoggingGovernanceEngine(InMemoryLogRetentionPolicyStore())


@lru_cache
def get_tracing_engine() -> TracingEngine:
    return TracingEngine(InMemorySpanStore())


@lru_cache
def get_telemetry_engine() -> TelemetryEngine:
    return TelemetryEngine(
        get_metrics_engine(), get_tracing_engine(), InMemoryTelemetryEventStore()
    )


@lru_cache
def get_alerting_engine() -> AlertingEngine:
    return AlertingEngine(
        InMemoryAlertRuleStore(),
        InMemoryAlertEventStore(),
        get_metrics_engine(),
        get_notification_engine(),
    )


@lru_cache
def get_dashboards_engine() -> DashboardsEngine:
    return DashboardsEngine(
        get_monitoring_engine(),
        get_metrics_engine(),
        get_connector_registry_engine(),
        get_model_registry(),
        get_quality_optimizer(),
        get_fallback_engine(),
        get_cost_tracker_engine(),
        get_identity_monitoring_engine(),
        get_analytics_engine(),
    )


@lru_cache
def ensure_business_context_health_checks_registered() -> HealthCheckEngine:
    """Registers the five business-context health checks the sprint
    names (AI Fabric, Marketplace, Workflow Engine, Identity Platform,
    Business Platform) into `platform.health`'s shared
    `HealthCheckEngine` singleton — the same one API/database/cache
    already register into — rather than a second aggregation engine.
    Called once via `lru_cache`, at first use."""
    engine = get_health_check_engine()
    register_business_context_health_checks(
        engine,
        model_registry=get_model_registry(),
        plugin_registry=get_plugin_registry(),
        workflow_engine=get_workflow_engine(),
        authorization_engine=get_authorization_engine(),
        subscription_engine=get_subscription_engine(),
    )
    return engine


@lru_cache
def get_sla_engine() -> SLAEngine:
    return SLAEngine(InMemorySLATargetStore(), InMemorySLASampleStore())


@lru_cache
def get_slo_engine() -> SLOEngine:
    return SLOEngine(InMemorySLOTargetStore(), get_sla_engine())


@lru_cache
def get_capacity_engine() -> CapacityEngine:
    return CapacityEngine(get_metrics_engine())


@lru_cache
def get_performance_engine() -> PerformanceEngine:
    return PerformanceEngine(get_metrics_engine())


@lru_cache
def get_profiling_engine() -> ProfilingEngine:
    return ProfilingEngine(InMemoryProfilingSampleStore())


@lru_cache
def get_cache_observability_engine() -> CacheObservabilityEngine:
    return CacheObservabilityEngine(get_metrics_engine())


@lru_cache
def get_queue_observability_engine() -> QueueObservabilityEngine:
    return QueueObservabilityEngine(get_metrics_engine())


@lru_cache
def get_error_tracking_engine() -> ErrorTrackingEngine:
    return ErrorTrackingEngine(InMemoryErrorEventStore(), get_metrics_engine())


@lru_cache
def get_incident_management_engine() -> IncidentManagementEngine:
    return IncidentManagementEngine(InMemoryIncidentStore(), InMemoryIncidentUpdateStore())


@lru_cache
def get_runbooks_engine() -> RunbooksEngine:
    return RunbooksEngine()


@lru_cache
def get_diagnostics_engine() -> DiagnosticsEngine:
    ensure_business_context_health_checks_registered()
    return DiagnosticsEngine(
        get_health_check_engine(),
        get_performance_engine(),
        get_error_tracking_engine(),
        get_tracing_engine(),
    )


@lru_cache
def get_circuit_breaker() -> CircuitBreaker:
    return CircuitBreaker()


@lru_cache
def get_chaos_testing_engine() -> ChaosTestingEngine:
    return ChaosTestingEngine(get_settings().environment, get_circuit_breaker())
