from tmis.case_intelligence.evaluation.evaluator import CaseEvaluator
from tmis.case_intelligence.evaluation.metrics import CaseUpdateMetrics, StepMetric


def test_error_count_counts_failed_steps() -> None:
    metrics = CaseUpdateMetrics(
        case_id="case-1",
        document_id="doc-1",
        total_duration_ms=10.0,
        step_metrics=(
            StepMetric(step="update_actors", duration_ms=1.0, success=True),
            StepMetric(step="update_facts", duration_ms=2.0, success=False, error="boom"),
        ),
    )
    assert metrics.error_count == 1


def test_error_count_is_zero_when_all_succeed() -> None:
    metrics = CaseUpdateMetrics(
        case_id="case-1",
        document_id="doc-1",
        total_duration_ms=5.0,
        step_metrics=(StepMetric(step="update_actors", duration_ms=1.0, success=True),),
    )
    assert metrics.error_count == 0


def test_evaluator_records_and_lists_history() -> None:
    evaluator = CaseEvaluator()
    metrics = CaseUpdateMetrics(case_id="case-1", document_id="doc-1", total_duration_ms=1.0)
    evaluator.record(metrics)
    assert evaluator.history == [metrics]


def test_evaluator_filters_by_case() -> None:
    evaluator = CaseEvaluator()
    metrics_a = CaseUpdateMetrics(case_id="case-a", document_id="doc-1", total_duration_ms=1.0)
    metrics_b = CaseUpdateMetrics(case_id="case-b", document_id="doc-2", total_duration_ms=2.0)
    evaluator.record(metrics_a)
    evaluator.record(metrics_b)

    assert evaluator.for_case("case-a") == [metrics_a]
