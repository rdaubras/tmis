from tmis.document_intelligence.evaluation.evaluator import PipelineEvaluator
from tmis.document_intelligence.evaluation.metrics import PipelineMetrics, StageMetric


def test_pipeline_metrics_error_count_counts_failed_stages() -> None:
    metrics = PipelineMetrics(
        document_id="doc-1",
        total_duration_ms=10.0,
        stage_metrics=(
            StageMetric(stage="validation", duration_ms=1.0, success=True),
            StageMetric(stage="ocr", duration_ms=2.0, success=False, error="boom"),
        ),
    )
    assert metrics.error_count == 1


def test_pipeline_metrics_error_count_is_zero_when_all_succeed() -> None:
    metrics = PipelineMetrics(
        document_id="doc-1",
        total_duration_ms=5.0,
        stage_metrics=(StageMetric(stage="validation", duration_ms=1.0, success=True),),
    )
    assert metrics.error_count == 0


def test_evaluator_records_and_lists_history() -> None:
    evaluator = PipelineEvaluator()
    metrics = PipelineMetrics(document_id="doc-1", total_duration_ms=1.0)
    evaluator.record(metrics)
    assert evaluator.history == [metrics]


def test_evaluator_filters_by_document() -> None:
    evaluator = PipelineEvaluator()
    metrics_a = PipelineMetrics(document_id="doc-a", total_duration_ms=1.0)
    metrics_b = PipelineMetrics(document_id="doc-b", total_duration_ms=2.0)
    evaluator.record(metrics_a)
    evaluator.record(metrics_b)

    assert evaluator.for_document("doc-a") == [metrics_a]
