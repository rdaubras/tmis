from tmis.legal_reasoning.evaluation.evaluator import ReasoningEvaluator
from tmis.legal_reasoning.evaluation.metrics import ReasoningMetrics


def _metrics(**overrides: object) -> ReasoningMetrics:
    defaults: dict[str, object] = dict(
        session_id="s1",
        duration_ms=10.0,
        modules_used=("hypotheses", "arguments"),
        average_confidence=0.5,
        hypothesis_count=2,
        argument_count=1,
        counter_argument_count=1,
        conflict_count=0,
    )
    defaults.update(overrides)
    return ReasoningMetrics(**defaults)  # type: ignore[arg-type]


def test_record_appends_to_history() -> None:
    evaluator = ReasoningEvaluator()
    evaluator.record(_metrics())
    assert len(evaluator.history) == 1


def test_average_duration_ms_is_zero_with_no_history() -> None:
    assert ReasoningEvaluator().average_duration_ms() == 0.0


def test_average_duration_ms() -> None:
    evaluator = ReasoningEvaluator()
    evaluator.record(_metrics(session_id="s1", duration_ms=10.0))
    evaluator.record(_metrics(session_id="s2", duration_ms=20.0))
    assert evaluator.average_duration_ms() == 15.0
