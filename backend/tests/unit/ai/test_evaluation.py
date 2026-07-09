from tmis.ai.evaluation.evaluator import Evaluator
from tmis.ai.evaluation.metrics import EvaluationMetrics, estimate_cost
from tmis.ai.evaluation.sinks import InMemoryEvaluationSink


def test_estimate_cost_uses_provider_rate() -> None:
    assert estimate_cost("openai", 1000) == 0.005
    assert estimate_cost("local", 1000) == 0.0


def test_estimate_cost_unknown_provider_uses_default_rate() -> None:
    assert estimate_cost("unknown-provider", 1000) == 0.005


def test_evaluator_records_to_default_sink() -> None:
    evaluator = Evaluator()
    metrics = EvaluationMetrics(
        provider="openai",
        model="gpt-4o",
        latency_ms=12.5,
        token_count=10,
        estimated_cost_usd=0.00005,
        confidence_score=0.9,
    )
    evaluator.record(metrics)
    assert evaluator.in_memory_metrics == [metrics]


def test_evaluator_fans_out_to_multiple_sinks() -> None:
    sink_a, sink_b = InMemoryEvaluationSink(), InMemoryEvaluationSink()
    evaluator = Evaluator(sinks=[sink_a, sink_b])
    metrics = EvaluationMetrics(
        provider="anthropic",
        model="claude-sonnet-5",
        latency_ms=5.0,
        token_count=3,
        estimated_cost_usd=0.0,
        confidence_score=1.0,
    )
    evaluator.record(metrics)
    assert sink_a.metrics == [metrics]
    assert sink_b.metrics == [metrics]
