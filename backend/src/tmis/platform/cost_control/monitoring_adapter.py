from tmis.platform.cost_control.ports import CostTrackerEnginePort


class CostTrackerSummaryAdapter:
    """Implements `tmis.platform.monitoring.ports.CostSummaryPort` on
    top of a `CostTrackerEnginePort` — the real adapter that replaces
    `NullCostSummaryPort` once cost tracking exists (see
    docs/49-guide-supervision.md)."""

    def __init__(self, cost_tracker: CostTrackerEnginePort) -> None:
        self._cost_tracker = cost_tracker

    def total_cost_usd(self) -> float:
        return self._cost_tracker.total_cost_usd()
