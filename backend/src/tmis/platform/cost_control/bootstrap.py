from functools import lru_cache

from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore


@lru_cache
def get_cost_entry_store() -> InMemoryCostEntryStore:
    """Process-wide `InMemoryCostEntryStore` singleton — split out
    from `get_cost_tracker_engine` so `business_platform.analytics.
    AnalyticsEngine` (Sprint 20) can read firm-scoped cost entries
    directly via `CostEntryStorePort`, the same store the tracker
    itself writes to."""
    return InMemoryCostEntryStore()


@lru_cache
def get_cost_tracker_engine() -> CostTrackerEngine:
    """Process-wide `CostTrackerEngine` singleton (see
    docs/50-guide-performance.md — Cost Control)."""
    return CostTrackerEngine(get_cost_entry_store(), InMemoryAlertThresholdStore())
