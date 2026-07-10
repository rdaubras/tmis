from tmis.legal_drafting.evaluation.evaluator import DraftEvaluator
from tmis.legal_drafting.evaluation.metrics import DraftMetrics


def _metrics(**overrides: object) -> DraftMetrics:
    defaults: dict[str, object] = dict(
        document_id="doc1",
        duration_ms=10.0,
        components_used=("templates", "paragraphs"),
        paragraph_count=3,
        reference_count=2,
        estimated_cost_usd=0.001,
        template_id="consultation:v1",
    )
    defaults.update(overrides)
    return DraftMetrics(**defaults)  # type: ignore[arg-type]


def test_record_appends_to_history() -> None:
    evaluator = DraftEvaluator()
    evaluator.record(_metrics())
    assert len(evaluator.history) == 1


def test_average_duration_ms_is_zero_with_no_history() -> None:
    assert DraftEvaluator().average_duration_ms() == 0.0


def test_average_duration_ms() -> None:
    evaluator = DraftEvaluator()
    evaluator.record(_metrics(document_id="d1", duration_ms=10.0))
    evaluator.record(_metrics(document_id="d2", duration_ms=20.0))
    assert evaluator.average_duration_ms() == 15.0


def test_total_estimated_cost_usd_sums_across_runs() -> None:
    evaluator = DraftEvaluator()
    evaluator.record(_metrics(document_id="d1", estimated_cost_usd=0.001))
    evaluator.record(_metrics(document_id="d2", estimated_cost_usd=0.002))
    assert round(evaluator.total_estimated_cost_usd(), 6) == 0.003
