from tmis.cloud_operations.sla.engine import SLAEngine
from tmis.cloud_operations.sla.schemas import _LOWER_IS_BETTER, SLAMetricType
from tmis.cloud_operations.slo.ports import SLOTargetStorePort
from tmis.cloud_operations.slo.schemas import SLOStatus, SLOTarget, new_slo_target_id

_AT_RISK_THRESHOLD_PERCENT = 20.0


class SLOEngine:
    """An SLO is an internal, usually-stricter cousin of an SLA (see
    `slo.schemas.SLOTarget`) — this engine reuses `sla.SLAEngine.
    average_value` for the underlying measurement rather than a
    second sampling/averaging mechanism; only the objective and the
    error-budget interpretation are SLO-specific."""

    def __init__(self, targets: SLOTargetStorePort, sla_engine: SLAEngine) -> None:
        self._targets = targets
        self._sla = sla_engine

    def set_objective(
        self, service_name: str, metric_type: SLAMetricType, objective_value: float
    ) -> SLOTarget:
        target = SLOTarget(
            id=new_slo_target_id(),
            service_name=service_name,
            metric_type=metric_type,
            objective_value=objective_value,
        )
        self._targets.save(target)
        return target

    def status(self, service_name: str, metric_type: SLAMetricType) -> SLOStatus | None:
        target = self._targets.get(service_name, metric_type)
        actual = self._sla.average_value(service_name, metric_type)
        if target is None or actual is None:
            return None
        if metric_type in _LOWER_IS_BETTER:
            met = actual <= target.objective_value
            remaining = 100.0 if met else 0.0
        else:
            error_budget_total = 100.0 - target.objective_value
            shortfall = max(0.0, target.objective_value - actual)
            remaining = (
                100.0 * (1 - shortfall / error_budget_total) if error_budget_total > 0 else 100.0
            )
            remaining = max(0.0, min(100.0, remaining))
        return SLOStatus(
            service_name=service_name,
            metric_type=metric_type,
            objective_value=target.objective_value,
            actual_value=actual,
            error_budget_remaining_percent=remaining,
            at_risk=remaining < _AT_RISK_THRESHOLD_PERCENT,
        )
