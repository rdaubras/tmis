import uuid
from datetime import UTC, datetime, timedelta

from tmis.ai.evaluation.metrics import estimate_cost
from tmis.platform.cost_control.ports import AlertThresholdStorePort, CostEntryStorePort
from tmis.platform.cost_control.schemas import AlertThreshold, CostBreach, CostEntry


class CostTrackerEngine:
    """Implements `CostTrackerEnginePort` (see
    docs/50-guide-performance.md — Cost Control). Reuses
    `tmis.ai.evaluation.metrics.estimate_cost` for the actual per-token
    pricing — the same model the Kernel itself uses to record
    `EvaluationMetrics.estimated_cost_usd` — so cost figures never
    drift between the two.

    **Known limitation**: `TMISKernel.complete()` does not yet accept
    or propagate a user/case/workflow context, so nothing calls
    `record()` automatically today; a caller wrapping a Kernel call
    must report the cost explicitly. This mirrors the same limitation
    already documented for `tmis.cabinet_os.analytics.AIUsagePort`
    (Sprint 9)."""

    def __init__(
        self, entry_store: CostEntryStorePort, threshold_store: AlertThresholdStorePort
    ) -> None:
        self._entries = entry_store
        self._thresholds = threshold_store

    def record(
        self,
        firm_id: str,
        user_id: str,
        provider: str,
        model: str,
        token_count: int,
        *,
        case_id: str | None = None,
        workflow_id: str | None = None,
        cache_hit: bool = False,
    ) -> CostEntry:
        cost_usd = 0.0 if cache_hit else estimate_cost(provider, token_count)
        entry = CostEntry(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            user_id=user_id,
            case_id=case_id,
            workflow_id=workflow_id,
            provider=provider,
            model=model,
            token_count=token_count,
            cost_usd=cost_usd,
            cache_hit=cache_hit,
            recorded_at=datetime.now(UTC),
        )
        self._entries.save(entry)
        return entry

    def cost_by_user(self, user_id: str) -> float:
        return sum(e.cost_usd for e in self._entries.list_for_user(user_id))

    def cost_by_case(self, case_id: str) -> float:
        return sum(e.cost_usd for e in self._entries.list_for_case(case_id))

    def cost_by_workflow(self, workflow_id: str) -> float:
        return sum(e.cost_usd for e in self._entries.list_for_workflow(workflow_id))

    def cost_by_provider(self, firm_id: str, provider: str) -> float:
        return sum(
            e.cost_usd for e in self._entries.list_for_firm(firm_id) if e.provider == provider
        )

    def total_cost_usd(self) -> float:
        return sum(e.cost_usd for e in self._entries.list_all())

    def cache_hit_rate(self, firm_id: str) -> float:
        entries = self._entries.list_for_firm(firm_id)
        if not entries:
            return 0.0
        return sum(1 for e in entries if e.cache_hit) / len(entries)

    def set_alert_threshold(
        self, scope: str, scope_id: str, max_cost_usd: float, period_days: int = 30
    ) -> AlertThreshold:
        threshold = AlertThreshold(
            scope=scope, scope_id=scope_id, max_cost_usd=max_cost_usd, period_days=period_days
        )
        self._thresholds.save(threshold)
        return threshold

    def check_thresholds(self, firm_id: str) -> list[CostBreach]:
        now = datetime.now(UTC)
        breaches: list[CostBreach] = []
        for threshold in self._thresholds.list_all():
            if threshold.scope == "firm" and threshold.scope_id == firm_id:
                entries = self._entries.list_for_firm(firm_id)
            elif threshold.scope == "user":
                entries = self._entries.list_for_user(threshold.scope_id)
            else:
                continue
            cutoff = now - timedelta(days=threshold.period_days)
            current_cost = sum(e.cost_usd for e in entries if e.recorded_at >= cutoff)
            if current_cost > threshold.max_cost_usd:
                breaches.append(
                    CostBreach(threshold=threshold, current_cost_usd=current_cost, checked_at=now)
                )
        return breaches
