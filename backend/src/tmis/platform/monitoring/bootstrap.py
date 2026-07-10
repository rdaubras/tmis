from functools import lru_cache

from tmis.platform.cost_control.bootstrap import get_cost_tracker_engine
from tmis.platform.cost_control.monitoring_adapter import CostTrackerSummaryAdapter
from tmis.platform.health.bootstrap import get_health_check_engine
from tmis.platform.metrics.bootstrap import get_metrics_registry
from tmis.platform.monitoring.engine import MonitoringEngine


@lru_cache
def get_monitoring_engine() -> MonitoringEngine:
    """Process-wide `MonitoringEngine` singleton — see
    docs/49-guide-supervision.md. Wired to the real
    `CostTrackerEngine` via `CostTrackerSummaryAdapter`."""
    return MonitoringEngine(
        get_health_check_engine(),
        get_metrics_registry(),
        CostTrackerSummaryAdapter(get_cost_tracker_engine()),
    )
