import time

from tmis.ai_fabric.governance.engine import GovernanceEngine
from tmis.ai_fabric.model_registry.ports import ModelRegistryPort
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.quotas.engine import QuotaEngine
from tmis.ai_fabric.router.schemas import (
    NoEligibleModelError,
    QuotaExceededError,
    RoutingDecision,
    RoutingRequest,
)

_QUOTA_SCOPE = "firm"


class RouterEngine:
    """The sprint's "ROUTER": selects the best-suited model for a
    request by task type, target cost, max time, quality level,
    subscription (firm quota), and availability — filtering through
    `tmis.ai_fabric.governance` policy first, since a forbidden model
    must never even be considered. Every filtering step is recorded
    into `RoutingDecision.reasons` so the choice stays explainable,
    per the sprint's own constraint."""

    def __init__(
        self,
        model_registry: ModelRegistryPort,
        governance_engine: GovernanceEngine,
        quota_engine: QuotaEngine,
    ) -> None:
        self._model_registry = model_registry
        self._governance_engine = governance_engine
        self._quota_engine = quota_engine

    def route(self, request: RoutingRequest) -> RoutingDecision:
        started = time.perf_counter()
        try:
            decision = self._route(request)
        except (NoEligibleModelError, QuotaExceededError) as exc:
            self._record_routing_error(request, exc)
            raise
        finally:
            self._record_routing_duration(request, (time.perf_counter() - started) * 1000)
        return decision

    def _route(self, request: RoutingRequest) -> RoutingDecision:
        reasons: list[str] = []

        candidates = (
            self._model_registry.list_by_profile(request.profile)
            if request.profile is not None
            else self._model_registry.list_all()
        )
        reasons.append(
            f"{len(candidates)} modèle(s) associés au profil "
            f"{request.profile.value if request.profile else 'quelconque'}"
        )

        candidates = self._filter_available(candidates, reasons)
        candidates = self._filter_quality(candidates, request.min_quality_score, reasons)
        candidates = self._filter_cost(candidates, request.target_cost_usd, reasons)
        candidates = self._filter_latency(candidates, request.max_latency_ms, reasons)
        candidates = self._filter_governance(candidates, request, reasons)

        if not candidates:
            raise NoEligibleModelError(request, tuple(reasons))

        if not self._quota_engine.check(_QUOTA_SCOPE, request.firm_id):
            raise QuotaExceededError(request.firm_id)

        best = max(
            candidates,
            key=lambda m: (m.quality_score, -m.cost_per_1k_tokens_usd, -m.avg_latency_ms),
        )
        reasons.append(
            f"modèle retenu : {best.name} (score qualité {best.quality_score:.2f}, "
            f"coût {best.cost_per_1k_tokens_usd}/1k tokens, latence {best.avg_latency_ms}ms)"
        )

        self._quota_engine.record_call(_QUOTA_SCOPE, request.firm_id)

        return RoutingDecision(model=best, reasons=tuple(reasons))

    def _record_routing_duration(self, request: RoutingRequest, duration_ms: float) -> None:
        """Publishes the "AI Fabric" hop of the sprint's end-to-end
        request trace: every routing decision (the mandatory gateway
        in front of any model call, per this class's own docstring)
        reports its own decision latency as an `AI_CALL_DURATION`
        sample. A local import avoids a hard dependency from
        `ai_fabric` on `cloud_operations` at module-import time."""
        from tmis.cloud_operations.bootstrap import get_metrics_engine
        from tmis.cloud_operations.metrics.schemas import MetricCategory

        get_metrics_engine().record(
            MetricCategory.AI_CALL_DURATION,
            "router.route",
            duration_ms,
            firm_id=request.firm_id,
        )

    def _record_routing_error(
        self, request: RoutingRequest, exc: NoEligibleModelError | QuotaExceededError
    ) -> None:
        from tmis.cloud_operations.bootstrap import get_error_tracking_engine

        get_error_tracking_engine().record(
            "ai_fabric", type(exc).__name__, str(exc), firm_id=request.firm_id
        )

    def _filter_available(
        self, candidates: list[ModelDescriptor], reasons: list[str]
    ) -> list[ModelDescriptor]:
        filtered = [m for m in candidates if m.availability]
        reasons.append(f"{len(filtered)} disponible(s) après filtrage de disponibilité")
        return filtered

    def _filter_quality(
        self, candidates: list[ModelDescriptor], min_quality_score: float, reasons: list[str]
    ) -> list[ModelDescriptor]:
        if min_quality_score <= 0.0:
            return candidates
        filtered = [m for m in candidates if m.quality_score >= min_quality_score]
        reasons.append(
            f"{len(filtered)} au-dessus du niveau de qualité minimal {min_quality_score:.2f}"
        )
        return filtered

    def _filter_cost(
        self, candidates: list[ModelDescriptor], target_cost_usd: float | None, reasons: list[str]
    ) -> list[ModelDescriptor]:
        if target_cost_usd is None:
            return candidates
        filtered = [m for m in candidates if m.cost_per_1k_tokens_usd <= target_cost_usd]
        reasons.append(f"{len(filtered)} sous le coût cible {target_cost_usd}/1k tokens")
        return filtered

    def _filter_latency(
        self, candidates: list[ModelDescriptor], max_latency_ms: float | None, reasons: list[str]
    ) -> list[ModelDescriptor]:
        if max_latency_ms is None:
            return candidates
        filtered = [m for m in candidates if m.avg_latency_ms <= max_latency_ms]
        reasons.append(f"{len(filtered)} sous le temps maximal {max_latency_ms}ms")
        return filtered

    def _filter_governance(
        self, candidates: list[ModelDescriptor], request: RoutingRequest, reasons: list[str]
    ) -> list[ModelDescriptor]:
        allowed: list[ModelDescriptor] = []
        for model in candidates:
            decision = self._governance_engine.evaluate(
                request.firm_id,
                model.name,
                request.country,
                request.data_type,
                record=False,
            )
            if decision.allowed:
                allowed.append(model)
            else:
                joined_reasons = "; ".join(decision.reasons)
                reasons.append(f"{model.name} exclu par la gouvernance : {joined_reasons}")
        return allowed
