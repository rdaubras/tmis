from tmis.legal_research.ranking.configurable_ranker import ConfigurableRanker
from tmis.legal_research.ranking.schemas import RankingWeights
from tmis.legal_research.search.schemas import ResearchResult
from tmis.legal_research.sources.registry import SourceRegistry


def _result(**overrides: object) -> ResearchResult:
    defaults: dict[str, object] = dict(
        id="r1",
        title="Result",
        excerpt="excerpt",
        connector="codes",
        document_type="code",
        reference="ref",
        date=None,
        lexical_score=0.0,
        vector_score=0.0,
    )
    defaults.update(overrides)
    return ResearchResult(**defaults)  # type: ignore[arg-type]


def test_rank_sorts_by_descending_final_score() -> None:
    ranker = ConfigurableRanker(SourceRegistry(), current_year_fn=lambda: 2026)
    low = _result(id="low", lexical_score=0.1, vector_score=0.1)
    high = _result(id="high", lexical_score=0.9, vector_score=0.9)

    ranked = ranker.rank([low, high])

    assert [r.id for r in ranked] == ["high", "low"]
    assert ranked[0].final_score >= ranked[1].final_score


def test_rank_sets_authority_score_from_registry() -> None:
    registry = SourceRegistry()
    ranker = ConfigurableRanker(registry, current_year_fn=lambda: 2026)
    result = _result(connector="codes")

    ranker.rank([result])

    assert result.authority_score == registry.authority_score("codes")


def test_rank_freshness_favours_recent_documents() -> None:
    ranker = ConfigurableRanker(SourceRegistry(), current_year_fn=lambda: 2026)
    recent = _result(id="recent", date="2025-01-01")
    old = _result(id="old", date="1980-01-01")

    ranker.rank([recent, old])

    assert recent.freshness_score > old.freshness_score


def test_rank_uses_neutral_freshness_when_date_is_missing() -> None:
    ranker = ConfigurableRanker(SourceRegistry(), current_year_fn=lambda: 2026)
    result = _result(date=None)

    ranker.rank([result])

    assert 0.0 < result.freshness_score < 1.0


def test_rank_respects_custom_weights() -> None:
    ranker = ConfigurableRanker(SourceRegistry(), current_year_fn=lambda: 2026)
    result = _result(lexical_score=1.0, vector_score=0.0, connector="doctrine", date=None)

    all_lexical = ranker.rank(
        [result], RankingWeights(lexical=1.0, vector=0.0, authority=0.0, freshness=0.0)
    )[0]
    assert all_lexical.final_score == 1.0
