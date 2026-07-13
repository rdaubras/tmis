from datetime import UTC, datetime

from tmis.ai_fabric.fallback.engine import FallbackEngine
from tmis.ai_fabric.model_registry.ports import ModelRegistryPort
from tmis.ai_fabric.quality_optimizer.engine import QualityOptimizer
from tmis.ai_fabric.telemetry.engine import TelemetryDashboard
from tmis.ai_fabric.telemetry.schemas import FabricTelemetry
from tmis.business_platform.analytics.engine import AnalyticsEngine
from tmis.business_platform.analytics.schemas import BusinessDashboard
from tmis.cloud_operations.dashboards.schemas import (
    IntegrationsDashboard,
    OperationsOverview,
    WorkflowsDashboard,
)
from tmis.cloud_operations.metrics.engine import MetricsEngine
from tmis.cloud_operations.metrics.schemas import MetricCategory
from tmis.identity_platform.monitoring.engine import IdentityMonitoringEngine
from tmis.identity_platform.monitoring.schemas import IdentityDashboard
from tmis.integration_hub.connector_registry.engine import ConnectorRegistryEngine
from tmis.integration_hub.health.engine import ConnectorHealthProbe
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.monitoring.engine import MonitoringEngine
from tmis.platform.monitoring.schemas import SupervisionDashboard


class DashboardsEngine:
    """The sprint's "tableaux de bord dédiés" — a pure read-only
    composition over every dashboard-producing engine already built
    (`platform.monitoring`, Sprint 10; `ai_fabric.telemetry`, Sprint
    14; `identity_platform.monitoring`, Sprint 19; `business_platform.
    analytics`, Sprint 20) plus `integration_hub.connector_registry`/
    `.health`, never a new source of truth for any of them. Only
    `workflows`/`integrations` are genuinely new views, built from
    `cloud_operations.metrics` history."""

    def __init__(
        self,
        monitoring: MonitoringEngine,
        metrics: MetricsEngine,
        connector_registry: ConnectorRegistryEngine,
        model_registry: ModelRegistryPort,
        quality_optimizer: QualityOptimizer,
        fallback_engine: FallbackEngine,
        cost_tracker: CostTrackerEngine,
        identity_monitoring: IdentityMonitoringEngine,
        business_analytics: AnalyticsEngine,
    ) -> None:
        self._monitoring = monitoring
        self._metrics = metrics
        self._connector_registry = connector_registry
        self._model_registry = model_registry
        self._quality_optimizer = quality_optimizer
        self._fallback_engine = fallback_engine
        self._cost_tracker = cost_tracker
        self._identity_monitoring = identity_monitoring
        self._business_analytics = business_analytics

    def platform_dashboard(self) -> SupervisionDashboard:
        return self._monitoring.snapshot()

    def workflows_dashboard(self, firm_id: str | None = None) -> WorkflowsDashboard:
        executed = self._metrics.history_for_category(MetricCategory.WORKFLOW_COUNT, firm_id)
        errors = [
            e
            for e in self._metrics.history_for_category(MetricCategory.ERRORS, firm_id)
            if e.labels.get("source") == "workflow_automation"
        ]
        return WorkflowsDashboard(
            firm_id=firm_id,
            total_workflows_executed=sum(e.value for e in executed),
            total_errors=sum(e.value for e in errors),
            computed_at=datetime.now(UTC),
        )

    def integrations_dashboard(self) -> IntegrationsDashboard:
        descriptors = self._connector_registry.list_connectors()
        healthy = sum(
            1 for d in descriptors if ConnectorHealthProbe(self._connector_registry, d.id)()
        )
        return IntegrationsDashboard(
            total_connectors=len(descriptors),
            healthy_connectors=healthy,
            computed_at=datetime.now(UTC),
        )

    def ai_dashboard(self, firm_id: str) -> FabricTelemetry:
        dashboard = TelemetryDashboard(
            self._model_registry,
            self._quality_optimizer,
            self._fallback_engine,
            self._cost_tracker,
            firm_id,
        )
        return dashboard.snapshot()

    def security_dashboard(self, firm_id: str) -> IdentityDashboard:
        return self._identity_monitoring.dashboard(firm_id)

    def business_dashboard(self, firm_id: str) -> BusinessDashboard:
        return self._business_analytics.build_dashboard(firm_id)

    def overview(self, firm_id: str | None = None) -> OperationsOverview:
        return OperationsOverview(
            firm_id=firm_id,
            platform=self.platform_dashboard(),
            workflows=self.workflows_dashboard(firm_id),
            integrations=self.integrations_dashboard(),
            ai=self.ai_dashboard(firm_id) if firm_id else None,
            security=self.security_dashboard(firm_id) if firm_id else None,
            business=self.business_dashboard(firm_id) if firm_id else None,
        )
