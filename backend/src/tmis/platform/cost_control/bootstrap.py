from functools import lru_cache

from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore


@lru_cache
def get_cost_tracker_engine() -> CostTrackerEngine:
    """Process-wide `CostTrackerEngine` singleton (see
    docs/50-guide-performance.md — Cost Control)."""
    return CostTrackerEngine(InMemoryCostEntryStore(), InMemoryAlertThresholdStore())
