from tmis.ai_fabric.benchmark.engine import BenchmarkEngine
from tmis.ai_fabric.benchmark.store import InMemoryBenchmarkStore
from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.fallback.engine import FallbackEngine
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.model_registry.store import InMemoryModelRegistry
from tmis.ai_fabric.quality_optimizer.engine import QualityOptimizer
from tmis.ai_fabric.quality_optimizer.store import InMemoryQualityStatsStore
from tmis.ai_fabric.telemetry.engine import TelemetryDashboard
from tmis.platform.cost_control.engine import CostTrackerEngine
from tmis.platform.cost_control.store import InMemoryAlertThresholdStore, InMemoryCostEntryStore

FIRM = "firm-a"


def _model(name: str, *, quality: float = 0.5) -> ModelDescriptor:
    return ModelDescriptor(
        name=name,
        version="1",
        provider="openai",
        cost_per_1k_tokens_usd=0.01,
        avg_latency_ms=500.0,
        max_context_tokens=8_000,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
        quality_score=quality,
    )


def test_benchmark_run_measures_quality_cost_latency_and_tokens() -> None:
    engine = BenchmarkEngine(InMemoryBenchmarkStore(), InMemoryModelRegistry())

    run = engine.run(
        "gpt-x", "Le contrat est valide. Art. 1103 s'applique.", cost_usd=0.02, latency_ms=800
    )

    assert run.model_name == "gpt-x"
    assert run.cost_usd == 0.02
    assert run.latency_ms == 800
    assert run.token_count > 0


def test_benchmark_run_feeds_the_model_registry_quality_score() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("gpt-x", quality=0.5))
    engine = BenchmarkEngine(InMemoryBenchmarkStore(), registry)

    engine.run(
        "gpt-x", "Le contrat est valide. Il produit ses effets.", cost_usd=0.01, latency_ms=500
    )

    model = registry.get("gpt-x")
    assert model is not None
    assert model.quality_score != 0.5


def test_benchmark_run_for_unregistered_model_does_not_raise() -> None:
    engine = BenchmarkEngine(InMemoryBenchmarkStore(), InMemoryModelRegistry())

    engine.run("unknown", "texte quelconque", cost_usd=0.0, latency_ms=100)  # must not raise


def test_benchmark_history_and_comparison_table() -> None:
    engine = BenchmarkEngine(InMemoryBenchmarkStore(), InMemoryModelRegistry())
    engine.run("gpt-x", "premier texte cohérent.", cost_usd=0.01, latency_ms=500)
    engine.run("gpt-x", "second texte cohérent.", cost_usd=0.01, latency_ms=500)
    engine.run("claude-y", "texte cohérent également.", cost_usd=0.01, latency_ms=500)

    assert len(engine.history("gpt-x")) == 2
    assert len(engine.comparison_table()) == 2


def _cost_tracker() -> CostTrackerEngine:
    return CostTrackerEngine(InMemoryCostEntryStore(), InMemoryAlertThresholdStore())


def test_telemetry_snapshot_includes_every_registered_model() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("gpt-x"))
    registry.register(_model("claude-y"))
    dashboard = TelemetryDashboard(
        registry,
        QualityOptimizer(InMemoryQualityStatsStore()),
        FallbackEngine(registry),
        _cost_tracker(),
        FIRM,
    )

    snapshot = dashboard.snapshot()

    assert {m.model_name for m in snapshot.models} == {"gpt-x", "claude-y"}


def test_telemetry_snapshot_usage_share_reflects_call_distribution() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("gpt-x"))
    registry.register(_model("claude-y"))
    quality_optimizer = QualityOptimizer(InMemoryQualityStatsStore())
    quality_optimizer.record_call("gpt-x", success=True)
    quality_optimizer.record_call("gpt-x", success=True)
    quality_optimizer.record_call("claude-y", success=True)
    dashboard = TelemetryDashboard(
        registry, quality_optimizer, FallbackEngine(registry), _cost_tracker(), FIRM
    )

    snapshot = dashboard.snapshot()

    gpt_x = next(m for m in snapshot.models if m.model_name == "gpt-x")
    claude_y = next(m for m in snapshot.models if m.model_name == "claude-y")
    assert gpt_x.usage_share == 2 / 3
    assert claude_y.usage_share == 1 / 3


def test_telemetry_snapshot_reflects_fallback_rate() -> None:
    registry = InMemoryModelRegistry()
    registry.register(_model("primary"))
    fallback_engine = FallbackEngine(registry)
    fallback_engine.resolve("missing", ("primary",))
    dashboard = TelemetryDashboard(
        registry,
        QualityOptimizer(InMemoryQualityStatsStore()),
        fallback_engine,
        _cost_tracker(),
        FIRM,
    )

    snapshot = dashboard.snapshot()

    assert snapshot.fallback_rate == 1.0
