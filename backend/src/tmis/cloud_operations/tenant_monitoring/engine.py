from tmis.business_platform.analytics.engine import AnalyticsEngine
from tmis.business_platform.usage.engine import UsageEngine
from tmis.cloud_operations.incident_management.engine import IncidentManagementEngine
from tmis.cloud_operations.tenant_monitoring.schemas import TenantMonitoringSnapshot


class TenantMonitoringEngine:
    """Per-cabinet dashboard composing `business_platform.analytics`,
    `business_platform.usage`, and `cloud_operations.
    incident_management` directly rather than a fourth per-tenant
    ledger."""

    def __init__(
        self,
        analytics: AnalyticsEngine,
        usage: UsageEngine,
        incidents: IncidentManagementEngine,
    ) -> None:
        self._analytics = analytics
        self._usage = usage
        self._incidents = incidents

    def snapshot(self, firm_id: str) -> TenantMonitoringSnapshot:
        dashboard = self._analytics.build_dashboard(firm_id)
        return TenantMonitoringSnapshot(
            firm_id=firm_id,
            monthly_recurring_revenue_usd=dashboard.monthly_recurring_revenue_usd,
            total_ai_cost_usd=dashboard.total_ai_cost_usd,
            active_modules_count=dashboard.active_modules_count,
            quota_usage=self._usage.full_snapshot(firm_id),
            open_incidents_count=len(self._incidents.open_incidents(firm_id)),
        )
