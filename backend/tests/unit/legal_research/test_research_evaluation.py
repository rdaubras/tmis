from tmis.legal_research.evaluation.evaluator import ResearchEvaluator
from tmis.legal_research.evaluation.metrics import ResearchMetrics


def _metrics(**overrides: object) -> ResearchMetrics:
    defaults: dict[str, object] = dict(
        search_id="s1",
        query="licenciement",
        search_time_ms=10.0,
        source_count=2,
        result_count=5,
        duplicate_rate=0.0,
        cache_hit=False,
        connectors_used=("codes", "jurisprudence"),
    )
    defaults.update(overrides)
    return ResearchMetrics(**defaults)  # type: ignore[arg-type]


def test_record_appends_to_history() -> None:
    evaluator = ResearchEvaluator()
    evaluator.record(_metrics())
    assert len(evaluator.history) == 1


def test_cache_hit_rate_is_zero_with_no_history() -> None:
    assert ResearchEvaluator().cache_hit_rate() == 0.0


def test_cache_hit_rate_reflects_recorded_runs() -> None:
    evaluator = ResearchEvaluator()
    evaluator.record(_metrics(search_id="s1", cache_hit=True))
    evaluator.record(_metrics(search_id="s2", cache_hit=False))

    assert evaluator.cache_hit_rate() == 0.5


def test_average_search_time_ms() -> None:
    evaluator = ResearchEvaluator()
    evaluator.record(_metrics(search_id="s1", search_time_ms=10.0))
    evaluator.record(_metrics(search_id="s2", search_time_ms=20.0))

    assert evaluator.average_search_time_ms() == 15.0
