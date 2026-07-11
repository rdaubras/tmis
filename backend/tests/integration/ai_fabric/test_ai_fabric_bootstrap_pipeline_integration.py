import pytest

from tmis.ai_fabric.bootstrap import (
    get_ai_intelligence_fabric,
    get_benchmark_engine,
    get_model_registry,
    get_quota_engine,
    get_task_planner,
    get_telemetry_dashboard,
)
from tmis.ai_fabric.governance.engine import GovernanceEngine
from tmis.ai_fabric.governance.store import InMemoryGovernanceStore
from tmis.ai_fabric.model_registry.store import InMemoryModelRegistry
from tmis.ai_fabric.planner.engine import TaskPlanner
from tmis.ai_fabric.planner.schemas import PlanStepKind
from tmis.ai_fabric.policies.store import InMemoryPolicyStore
from tmis.ai_fabric.quotas.engine import QuotaEngine
from tmis.ai_fabric.quotas.store import InMemoryQuotaStore
from tmis.ai_fabric.router.engine import RouterEngine
from tmis.ai_fabric.router.schemas import NoEligibleModelError, QuotaExceededError, RoutingRequest
from tmis.platform.licensing.bootstrap import get_license_engine


def test_bootstrap_seeds_a_model_for_every_default_pipeline_profile() -> None:
    registry = get_model_registry()

    plan = get_task_planner().plan("firm-pipeline-1", "Analyser le contrat de bail.")

    routed_steps = [s for s in plan.steps if s.sub_task.kind is not PlanStepKind.CRITIQUE]
    assert len(routed_steps) == 5
    assert all(s.decision is not None for s in routed_steps)
    assert all(registry.get(s.decision.model.name) is not None for s in routed_steps)  # type: ignore[union-attr]


def test_benchmark_result_is_visible_in_the_telemetry_snapshot() -> None:
    benchmark_engine = get_benchmark_engine()
    firm_id = "firm-pipeline-2"

    benchmark_engine.run(
        "gpt-4-legal",
        "Le contrat est valide. Art. 1103 du Code civil s'applique.",
        cost_usd=0.02,
        latency_ms=900,
    )

    snapshot = get_telemetry_dashboard(firm_id).snapshot()
    row = next(m for m in snapshot.models if m.model_name == "gpt-4-legal")
    assert row.quality_score > 0.0


def test_quota_blocks_routing_once_the_firm_limit_is_reached() -> None:
    fabric = get_ai_intelligence_fabric()
    quota_engine = get_quota_engine()
    firm_id = "firm-pipeline-quota"
    quota_engine.set_quota("firm", firm_id, max_calls_per_period=1, period_days=1)
    request = RoutingRequest(firm_id, "Rédaction", "rédige un avis", profile=None)

    fabric.route(request)

    with pytest.raises(QuotaExceededError):
        fabric.route(request)


def test_fabric_end_to_end_route_review_and_fuse() -> None:
    fabric = get_ai_intelligence_fabric()
    firm_id = "firm-pipeline-e2e"

    decision = fabric.route(RoutingRequest(firm_id, "Rédaction", "rédige un avis", profile=None))
    verdict = fabric.review(decision.model.name, "Le contrat est valide.")

    assert verdict.model_name == decision.model.name
    assert verdict.quality_score >= 0.0


def test_planner_raises_when_no_model_covers_a_required_profile() -> None:
    empty_registry = InMemoryModelRegistry()
    governance = GovernanceEngine(
        InMemoryPolicyStore(), InMemoryGovernanceStore(), get_license_engine()
    )
    router = RouterEngine(empty_registry, governance, QuotaEngine(InMemoryQuotaStore()))
    planner = TaskPlanner(router)

    with pytest.raises(NoEligibleModelError):
        planner.plan("firm-empty", "tâche impossible")
