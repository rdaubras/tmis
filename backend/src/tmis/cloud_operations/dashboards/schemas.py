from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.ai_fabric.telemetry.schemas import FabricTelemetry
from tmis.business_platform.analytics.schemas import BusinessDashboard
from tmis.identity_platform.monitoring.schemas import IdentityDashboard
from tmis.platform.monitoring.schemas import SupervisionDashboard


@dataclass(frozen=True, slots=True)
class WorkflowsDashboard:
    """No prior sprint built a workflow-specific operational
    dashboard — `workflow_automation.metrics.WorkflowRunMetrics` is a
    per-run record, not an aggregated view — so this one is
    genuinely new, built from `cloud_operations.metrics` history
    rather than a second counting mechanism."""

    firm_id: str | None
    total_workflows_executed: float
    total_errors: float
    computed_at: datetime


@dataclass(frozen=True, slots=True)
class IntegrationsDashboard:
    total_connectors: int
    healthy_connectors: int
    computed_at: datetime


@dataclass(frozen=True, slots=True)
class OperationsOverview:
    """The sprint's "tableaux de bord dédiés : plateforme, IA,
    workflows, intégrations, sécurité, Business Platform" in one
    read — `ai`/`security`/`business` are only populated for a
    firm-scoped view (`firm_id` given); the global view only has
    `platform`/`workflows`/`integrations`, which have no single-firm
    meaning."""

    firm_id: str | None
    platform: SupervisionDashboard
    workflows: WorkflowsDashboard
    integrations: IntegrationsDashboard
    ai: FabricTelemetry | None
    security: IdentityDashboard | None
    business: BusinessDashboard | None
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
