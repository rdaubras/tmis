from datetime import UTC, datetime

from tmis.business_platform.analytics.engine import AnalyticsEngine
from tmis.business_platform.reports.schemas import BusinessReport, new_report_id


class ReportEngine:
    """Turns a live `analytics.BusinessDashboard` into a frozen,
    timestamped `BusinessReport` — composes `AnalyticsEngine` rather
    than recomputing any figure itself."""

    def __init__(self, analytics: AnalyticsEngine) -> None:
        self._analytics = analytics

    def generate(self, firm_id: str) -> BusinessReport:
        dashboard = self._analytics.build_dashboard(firm_id)
        sections = {
            "plan": dashboard.plan_name.value,
            "monthly_recurring_revenue_usd": f"{dashboard.monthly_recurring_revenue_usd:.2f}",
            "total_ai_cost_usd": f"{dashboard.total_ai_cost_usd:.2f}",
            "cache_hit_rate": f"{dashboard.cache_hit_rate:.2%}",
            "cache_savings_usd": f"{dashboard.cache_savings_usd:.2f}",
            "active_modules_count": str(dashboard.active_modules_count),
            **{
                f"usage.{snapshot.dimension.value}": str(snapshot.used)
                for snapshot in dashboard.usage
            },
        }
        return BusinessReport(
            id=new_report_id(),
            firm_id=firm_id,
            generated_at=datetime.now(UTC),
            sections=sections,
        )
