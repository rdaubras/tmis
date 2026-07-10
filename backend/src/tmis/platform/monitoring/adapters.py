class NullCostSummaryPort:
    """Implements `CostSummaryPort`: reports zero cost — the default
    until `tmis.platform.cost_control` is wired in (see
    docs/49-guide-supervision.md)."""

    def total_cost_usd(self) -> float:
        return 0.0
