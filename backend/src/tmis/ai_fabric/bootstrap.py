from functools import lru_cache

from tmis.ai.cache.factory import make_cache
from tmis.ai.prompts.registry import PromptRegistry
from tmis.ai_fabric.benchmark.engine import BenchmarkEngine
from tmis.ai_fabric.benchmark.store import InMemoryBenchmarkStore
from tmis.ai_fabric.cache.engine import ResponseCache
from tmis.ai_fabric.comparison.engine import ComparisonEngine
from tmis.ai_fabric.consensus.engine import ConsensusEngine
from tmis.ai_fabric.cost_optimizer.engine import CostOptimizer
from tmis.ai_fabric.critic.engine import CriticModel
from tmis.ai_fabric.evaluation.engine import ResponseEvaluator
from tmis.ai_fabric.fabric import AIIntelligenceFabric
from tmis.ai_fabric.fallback.engine import FallbackEngine
from tmis.ai_fabric.fusion.engine import FusionEngine
from tmis.ai_fabric.governance.engine import GovernanceEngine
from tmis.ai_fabric.governance.store import InMemoryGovernanceStore
from tmis.ai_fabric.latency_optimizer.engine import LatencyOptimizer
from tmis.ai_fabric.model_registry.seed import seed_default_models
from tmis.ai_fabric.model_registry.store import InMemoryModelRegistry
from tmis.ai_fabric.planner.engine import TaskPlanner
from tmis.ai_fabric.policies.store import InMemoryPolicyStore
from tmis.ai_fabric.prompt_optimizer.engine import PromptOptimizer
from tmis.ai_fabric.provider_registry import FabricProviderRegistry
from tmis.ai_fabric.quality_optimizer.engine import QualityOptimizer
from tmis.ai_fabric.quality_optimizer.store import InMemoryQualityStatsStore
from tmis.ai_fabric.quotas.engine import QuotaEngine
from tmis.ai_fabric.quotas.store import InMemoryQuotaStore
from tmis.ai_fabric.retry.engine import RetryPolicy
from tmis.ai_fabric.router.engine import RouterEngine
from tmis.ai_fabric.streaming.engine import StreamingService
from tmis.ai_fabric.telemetry.engine import TelemetryDashboard
from tmis.ai_fabric.token_manager.engine import TokenManager
from tmis.platform.cost_control.bootstrap import get_cost_tracker_engine
from tmis.platform.licensing.bootstrap import get_license_engine


@lru_cache
def get_model_registry() -> InMemoryModelRegistry:
    """Process-wide composition root for `tmis.ai_fabric` (see
    docs/73-architecture-ai-fabric.md). Seeded once with a
    representative model catalog so the router has real choices."""
    registry = InMemoryModelRegistry()
    seed_default_models(registry)
    return registry


@lru_cache
def get_fabric_provider_registry() -> FabricProviderRegistry:
    return FabricProviderRegistry()


@lru_cache
def get_policy_store() -> InMemoryPolicyStore:
    return InMemoryPolicyStore()


@lru_cache
def get_governance_store() -> InMemoryGovernanceStore:
    return InMemoryGovernanceStore()


@lru_cache
def get_governance_engine() -> GovernanceEngine:
    return GovernanceEngine(get_policy_store(), get_governance_store(), get_license_engine())


@lru_cache
def get_quota_store() -> InMemoryQuotaStore:
    return InMemoryQuotaStore()


@lru_cache
def get_quota_engine() -> QuotaEngine:
    return QuotaEngine(get_quota_store())


@lru_cache
def get_token_manager() -> TokenManager:
    return TokenManager(get_cost_tracker_engine())


@lru_cache
def get_response_cache() -> ResponseCache:
    return ResponseCache(make_cache())


@lru_cache
def get_prompt_registry() -> PromptRegistry:
    return PromptRegistry()


@lru_cache
def get_prompt_optimizer() -> PromptOptimizer:
    return PromptOptimizer(get_prompt_registry())


@lru_cache
def get_response_evaluator() -> ResponseEvaluator:
    return ResponseEvaluator()


@lru_cache
def get_critic_model() -> CriticModel:
    return CriticModel(get_response_evaluator())


@lru_cache
def get_comparison_engine() -> ComparisonEngine:
    return ComparisonEngine(get_response_evaluator())


@lru_cache
def get_consensus_engine() -> ConsensusEngine:
    return ConsensusEngine()


@lru_cache
def get_fusion_engine() -> FusionEngine:
    return FusionEngine(get_response_evaluator())


@lru_cache
def get_cost_optimizer() -> CostOptimizer:
    return CostOptimizer(get_response_cache())


@lru_cache
def get_latency_optimizer() -> LatencyOptimizer:
    return LatencyOptimizer()


@lru_cache
def get_quality_stats_store() -> InMemoryQualityStatsStore:
    return InMemoryQualityStatsStore()


@lru_cache
def get_quality_optimizer() -> QualityOptimizer:
    return QualityOptimizer(get_quality_stats_store())


@lru_cache
def get_fallback_engine() -> FallbackEngine:
    return FallbackEngine(get_model_registry())


@lru_cache
def get_retry_policy() -> RetryPolicy:
    return RetryPolicy()


@lru_cache
def get_streaming_service() -> StreamingService:
    return StreamingService()


@lru_cache
def get_benchmark_store() -> InMemoryBenchmarkStore:
    return InMemoryBenchmarkStore()


@lru_cache
def get_benchmark_engine() -> BenchmarkEngine:
    return BenchmarkEngine(get_benchmark_store(), get_model_registry(), get_response_evaluator())


@lru_cache
def get_router_engine() -> RouterEngine:
    return RouterEngine(get_model_registry(), get_governance_engine(), get_quota_engine())


@lru_cache
def get_task_planner() -> TaskPlanner:
    return TaskPlanner(get_router_engine())


@lru_cache
def get_ai_intelligence_fabric() -> AIIntelligenceFabric:
    return AIIntelligenceFabric(
        get_router_engine(),
        get_task_planner(),
        get_critic_model(),
        get_comparison_engine(),
        get_consensus_engine(),
        get_fusion_engine(),
    )


def get_telemetry_dashboard(firm_id: str) -> TelemetryDashboard:
    """Not `@lru_cache`d, unlike every other factory here: it is
    parameterized by `firm_id` (needed for the per-firm
    `cache_hit_rate` read from `tmis.platform.cost_control`), so
    caching it process-wide would leak one firm's dashboard instance
    to every other firm."""
    return TelemetryDashboard(
        get_model_registry(),
        get_quality_optimizer(),
        get_fallback_engine(),
        get_cost_tracker_engine(),
        firm_id,
    )
