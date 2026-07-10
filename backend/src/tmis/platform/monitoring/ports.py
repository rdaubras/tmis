from typing import Protocol

from tmis.platform.monitoring.schemas import SupervisionDashboard


class CostSummaryPort(Protocol):
    """Narrow port into AI cost tracking — kept separate from
    `tmis.platform.cost_control` so `monitoring` never has to import
    it directly (see docs/49-guide-supervision.md); a real adapter is
    wired in at bootstrap time once cost tracking is recording data."""

    def total_cost_usd(self) -> float: ...


class MonitoringEnginePort(Protocol):
    """Port implemented by every interchangeable supervision engine."""

    def snapshot(self) -> SupervisionDashboard: ...
