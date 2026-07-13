from tmis.cloud_operations.cost_monitoring.schemas import CostMonitoringSnapshot
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.ports import CostEntryStorePort


class CostMonitoringEngine:
    """Specialized cost-monitoring facade over `platform.cost_control.
    CostTrackerEngine` (Sprint 10) — composes it and its entry store
    directly rather than a second cost ledger. `CostTrackerEngine`
    already tracks cost by user/case/workflow/provider; this engine
    adds the per-model/per-user breakdown and threshold-breach count
    the sprint's "coût par modèle" requirement asks for, by grouping
    the same underlying `CostEntry` rows."""

    def __init__(self, cost_tracker: CostTrackerEngine, entry_store: CostEntryStorePort) -> None:
        self._cost_tracker = cost_tracker
        self._entry_store = entry_store

    def snapshot(self, firm_id: str) -> CostMonitoringSnapshot:
        entries = self._entry_store.list_for_firm(firm_id)
        by_model: dict[str, float] = {}
        by_user: dict[str, float] = {}
        for entry in entries:
            by_model[entry.model] = by_model.get(entry.model, 0.0) + entry.cost_usd
            by_user[entry.user_id] = by_user.get(entry.user_id, 0.0) + entry.cost_usd
        return CostMonitoringSnapshot(
            firm_id=firm_id,
            total_cost_usd=sum(e.cost_usd for e in entries),
            cost_by_model=by_model,
            cost_by_user=by_user,
            cache_hit_rate=self._cost_tracker.cache_hit_rate(firm_id),
            breach_count=len(self._cost_tracker.check_thresholds(firm_id)),
        )
