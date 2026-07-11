import pytest

from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.comparison.engine import ComparisonEngine
from tmis.ai_fabric.consensus.engine import ConsensusEngine
from tmis.ai_fabric.critic.engine import CriticModel
from tmis.ai_fabric.fabric import AIIntelligenceFabric
from tmis.ai_fabric.fusion.engine import FusionEngine
from tmis.ai_fabric.governance.engine import GovernanceEngine
from tmis.ai_fabric.governance.store import InMemoryGovernanceStore
from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.model_registry.store import InMemoryModelRegistry
from tmis.ai_fabric.planner.engine import TaskPlanner
from tmis.ai_fabric.planner.schemas import PlanStepKind
from tmis.ai_fabric.policies.schemas import Policy, PolicyType, new_policy_id
from tmis.ai_fabric.policies.store import InMemoryPolicyStore
from tmis.ai_fabric.quotas.engine import QuotaEngine
from tmis.ai_fabric.quotas.store import InMemoryQuotaStore
from tmis.ai_fabric.router.engine import RouterEngine
from tmis.ai_fabric.router.schemas import NoEligibleModelError, QuotaExceededError, RoutingRequest
from tmis.platform.licensing.bootstrap import get_license_engine

FIRM = "firm-a"


def _model(
    name: str, *, profile: ModelProfile, quality: float = 0.7, available: bool = True
) -> ModelDescriptor:
    return ModelDescriptor(
        name=name,
        version="1",
        provider="openai",
        cost_per_1k_tokens_usd=0.01,
        avg_latency_ms=500.0,
        max_context_tokens=8_000,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
        profiles=frozenset({profile}),
        availability=available,
        quality_score=quality,
    )


def _router(registry: InMemoryModelRegistry) -> RouterEngine:
    governance = GovernanceEngine(
        InMemoryPolicyStore(), InMemoryGovernanceStore(), get_license_engine()
    )
    return RouterEngine(registry, governance, QuotaEngine(InMemoryQuotaStore()))


def test_router_picks_the_highest_quality_available_model() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("weak", profile=ModelProfile.DRAFTING, quality=0.5))
    registry.register(_model("strong", profile=ModelProfile.DRAFTING, quality=0.9))
    router = _router(registry)

    decision = router.route(
        RoutingRequest(FIRM, "Rédaction", "rédige un avis", profile=ModelProfile.DRAFTING)
    )

    assert decision.model.name == "strong"
    assert decision.reasons


def test_router_decision_is_explainable() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("only", profile=ModelProfile.DRAFTING))
    router = _router(registry)

    decision = router.route(RoutingRequest(FIRM, "Rédaction", "x", profile=ModelProfile.DRAFTING))

    assert any("retenu" in r for r in decision.reasons)


def test_router_filters_out_unavailable_models() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("down", profile=ModelProfile.DRAFTING, available=False))
    router = _router(registry)

    with pytest.raises(NoEligibleModelError):
        router.route(RoutingRequest(FIRM, "Rédaction", "x", profile=ModelProfile.DRAFTING))


def test_router_respects_target_cost() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("expensive", profile=ModelProfile.DRAFTING))
    router = _router(registry)

    with pytest.raises(NoEligibleModelError):
        router.route(
            RoutingRequest(
                FIRM, "Rédaction", "x", profile=ModelProfile.DRAFTING, target_cost_usd=0.001
            )
        )


def test_router_excludes_models_forbidden_by_governance() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("forbidden", profile=ModelProfile.DRAFTING))
    policy_store = InMemoryPolicyStore()
    policy_store.add(
        Policy(
            id=new_policy_id(),
            type=PolicyType.MODEL_FORBIDDEN,
            model_name="forbidden",
            reason="test",
        )
    )
    governance = GovernanceEngine(policy_store, InMemoryGovernanceStore(), get_license_engine())
    router = RouterEngine(registry, governance, QuotaEngine(InMemoryQuotaStore()))

    with pytest.raises(NoEligibleModelError):
        router.route(RoutingRequest(FIRM, "Rédaction", "x", profile=ModelProfile.DRAFTING))


def test_router_raises_quota_exceeded_once_limit_is_reached() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("gpt-x", profile=ModelProfile.DRAFTING))
    governance = GovernanceEngine(
        InMemoryPolicyStore(), InMemoryGovernanceStore(), get_license_engine()
    )
    quota_engine = QuotaEngine(InMemoryQuotaStore())
    quota_engine.set_quota("firm", FIRM, max_calls_per_period=1, period_days=1)
    router = RouterEngine(registry, governance, quota_engine)
    request = RoutingRequest(FIRM, "Rédaction", "x", profile=ModelProfile.DRAFTING)

    router.route(request)

    with pytest.raises(QuotaExceededError):
        router.route(request)


def test_planner_follows_the_sprint_default_pipeline() -> None:
    registry = InMemoryModelRegistry()
    for profile in (
        ModelProfile.VISION,
        ModelProfile.OCR,
        ModelProfile.SYNTHESIS,
        ModelProfile.REASONING,
        ModelProfile.DRAFTING,
    ):
        registry.register(_model(f"model-{profile.value}", profile=profile))
    planner = TaskPlanner(_router(registry))

    plan = planner.plan(FIRM, "Analyser le contrat et rédiger un avis.")

    assert [s.sub_task.name for s in plan.steps] == [
        "Analyse documentaire",
        "Extraction",
        "Recherche",
        "Raisonnement",
        "Rédaction",
        "Contrôle",
    ]
    assert plan.steps[-1].sub_task.kind is PlanStepKind.CRITIQUE
    assert plan.steps[-1].decision is None
    assert all(s.decision is not None for s in plan.steps[:-1])


def test_planner_propagates_router_failure() -> None:
    planner = TaskPlanner(_router(InMemoryModelRegistry()))

    with pytest.raises(NoEligibleModelError):
        planner.plan(FIRM, "tâche impossible")


def test_ai_intelligence_fabric_composes_router_planner_and_evaluation_tools() -> None:
    registry = InMemoryModelRegistry()
    for profile in (
        ModelProfile.VISION,
        ModelProfile.OCR,
        ModelProfile.SYNTHESIS,
        ModelProfile.REASONING,
        ModelProfile.DRAFTING,
    ):
        registry.register(_model(f"model-{profile.value}", profile=profile))
    router = _router(registry)
    fabric = AIIntelligenceFabric(
        router,
        TaskPlanner(router),
        CriticModel(),
        ComparisonEngine(),
        ConsensusEngine(),
        FusionEngine(),
    )

    plan = fabric.plan(FIRM, "Analyser le contrat.")
    verdict = fabric.review("model-drafting", "Le contrat est valide.")

    assert len(plan.steps) == 6
    assert verdict.model_name == "model-drafting"
