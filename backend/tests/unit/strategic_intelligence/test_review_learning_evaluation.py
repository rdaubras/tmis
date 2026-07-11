from tmis.ai_governance.bootstrap import get_human_validation_engine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType
from tmis.strategic_intelligence.evaluation.engine import StrategicIntelligenceEvaluator
from tmis.strategic_intelligence.evaluation.schemas import StrategyGenerationMetrics
from tmis.strategic_intelligence.evaluation.sinks import InMemoryStrategicMetricsSink
from tmis.strategic_intelligence.learning.engine import LearningEngine
from tmis.strategic_intelligence.learning.schemas import StrategyOutcome
from tmis.strategic_intelligence.learning.store import InMemoryLearningStore
from tmis.strategic_intelligence.review.adapter import StrategyReviewAdapter


def test_review_adapter_reuses_human_validation_engine() -> None:
    adapter = StrategyReviewAdapter(get_human_validation_engine())

    request = adapter.request_review("firm-review-test", "strategy-1", "avocat-1", ("associe-1",))
    assert adapter.is_validated("firm-review-test", "strategy-1") is False

    adapter.decide("firm-review-test", request.id, "associe-1", ValidationDecisionType.APPROVE)

    assert adapter.is_validated("firm-review-test", "strategy-1") is True


def test_review_adapter_history_lists_all_requests() -> None:
    adapter = StrategyReviewAdapter(get_human_validation_engine())

    adapter.request_review("firm-review-history", "strategy-2", "avocat-1", ("a",))
    adapter.request_review("firm-review-history", "strategy-2", "avocat-1", ("b",))

    assert len(adapter.history("firm-review-history", "strategy-2")) == 2


def test_learning_engine_records_outcome() -> None:
    engine = LearningEngine(InMemoryLearningStore())

    record = engine.record_outcome(
        "firm-1", "case-1", "strategy-1", "Négociation amiable", StrategyOutcome.CHOSEN, "avocat-1"
    )

    assert record.outcome is StrategyOutcome.CHOSEN
    assert engine.history_for_case("firm-1", "case-1") == [record]


def test_learning_engine_acceptance_rate_by_type() -> None:
    engine = LearningEngine(InMemoryLearningStore())
    engine.record_outcome(
        "firm-1", "case-1", "s1", "Négociation amiable", StrategyOutcome.CHOSEN, "a"
    )
    engine.record_outcome(
        "firm-1", "case-2", "s2", "Négociation amiable", StrategyOutcome.REJECTED, "a"
    )
    engine.record_outcome(
        "firm-1", "case-3", "s3", "Action prud'homale", StrategyOutcome.VALIDATED, "a"
    )

    rates = engine.acceptance_rate_by_type("firm-1")

    assert rates["Négociation amiable"] == 0.5
    assert rates["Action prud'homale"] == 1.0


def test_evaluator_fans_out_to_every_registered_sink() -> None:
    sink_a = InMemoryStrategicMetricsSink()
    sink_b = InMemoryStrategicMetricsSink()
    evaluator = StrategicIntelligenceEvaluator([sink_a, sink_b])

    evaluator.record(
        StrategyGenerationMetrics(
            case_id="case-1", strategy_count=4, duration_ms=12.5, playbooks_reused=1
        )
    )

    assert len(sink_a.all()) == 1
    assert len(sink_b.all()) == 1


def test_evaluator_with_no_sinks_does_not_raise() -> None:
    evaluator = StrategicIntelligenceEvaluator()

    evaluator.record(
        StrategyGenerationMetrics(
            case_id="case-1", strategy_count=1, duration_ms=1.0, playbooks_reused=0
        )
    )
