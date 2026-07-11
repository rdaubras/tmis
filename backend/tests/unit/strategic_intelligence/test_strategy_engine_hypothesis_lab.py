import pytest

from tmis.strategic_intelligence.hypothesis_lab.engine import HypothesisLabEngine
from tmis.strategic_intelligence.hypothesis_lab.schemas import InvalidHypothesisTransitionError
from tmis.strategic_intelligence.hypothesis_lab.store import InMemoryHypothesisLabStore
from tmis.strategic_intelligence.strategy_engine.engine import StrategyEngine
from tmis.strategic_intelligence.strategy_engine.schemas import DEFAULT_STRATEGY_TYPES


def test_strategy_engine_generates_one_strategy_per_candidate_type() -> None:
    engine = StrategyEngine()

    strategies = engine.generate(case_id="case-1", question="Comment défendre ce salarié ?")

    assert len(strategies) == len(DEFAULT_STRATEGY_TYPES)
    assert {s.strategy_type for s in strategies} == set(DEFAULT_STRATEGY_TYPES)


def test_strategy_engine_never_excludes_a_strategy() -> None:
    engine = StrategyEngine()

    strategies = engine.generate(
        case_id="case-1",
        question="q",
        counter_arguments=("a", "b", "c", "d", "e"),
        missing_evidence=("x", "y", "z"),
    )

    assert len(strategies) == len(DEFAULT_STRATEGY_TYPES)


def test_strategy_engine_always_attaches_a_limitation_disclaimer() -> None:
    engine = StrategyEngine()

    strategies = engine.generate(case_id="case-1", question="q")

    for strategy in strategies:
        assert strategy.limitations
        assert "décision juridique définitive" in strategy.limitations[-1]


def test_strategy_engine_respects_custom_candidate_types() -> None:
    engine = StrategyEngine()

    strategies = engine.generate(
        case_id="case-1", question="q", candidate_types=("Stratégie sur mesure",)
    )

    assert len(strategies) == 1
    assert strategies[0].strategy_type == "Stratégie sur mesure"


def test_strategy_engine_confidence_decreases_with_more_counter_arguments() -> None:
    engine = StrategyEngine()

    low_counter = engine.generate(
        case_id="case-1",
        question="q",
        candidate_types=("t",),
        available_evidence=("a", "b"),
    )[0]
    high_counter = engine.generate(
        case_id="case-1",
        question="q",
        candidate_types=("t",),
        available_evidence=("a", "b"),
        counter_arguments=("c1", "c2", "c3"),
    )[0]

    assert high_counter.confidence < low_counter.confidence


def test_hypothesis_lab_create_and_list_for_case() -> None:
    engine = HypothesisLabEngine(InMemoryHypothesisLabStore())

    engine.create("firm-1", "case-1", "Hypothèse A")
    engine.create("firm-1", "case-1", "Hypothèse B")
    engine.create("firm-1", "case-2", "Hypothèse autre dossier")

    assert len(engine.list_for_case("firm-1", "case-1")) == 2


def test_hypothesis_lab_compare_computes_jaccard_similarity() -> None:
    engine = HypothesisLabEngine(InMemoryHypothesisLabStore())
    a = engine.create("firm-1", "case-1", "Licenciement sans cause réelle")
    b = engine.create("firm-1", "case-1", "Licenciement pour faute grave")

    comparison = engine.compare("firm-1", a.id, b.id)

    assert 0.0 <= comparison.similarity <= 1.0
    assert "licenciement" in comparison.shared_terms


def test_hypothesis_lab_merge_marks_originals_merged_and_creates_new() -> None:
    engine = HypothesisLabEngine(InMemoryHypothesisLabStore())
    a = engine.create("firm-1", "case-1", "Hypothèse A")
    b = engine.create("firm-1", "case-1", "Hypothèse B")

    merged = engine.merge("firm-1", a.id, b.id, actor="avocat-1")

    assert engine.get("firm-1", a.id).status.value == "merged"
    assert engine.get("firm-1", b.id).status.value == "merged"
    assert merged.parent_ids == (a.id, b.id)


def test_hypothesis_lab_invalidate_records_reason_in_history() -> None:
    engine = HypothesisLabEngine(InMemoryHypothesisLabStore())
    hyp = engine.create("firm-1", "case-1", "Hypothèse A")

    engine.invalidate("firm-1", hyp.id, actor="avocat-1", reason="Non corroborée")

    history = engine.history("firm-1", hyp.id)
    assert len(history) == 1
    assert history[0].reason == "Non corroborée"
    assert history[0].to_status.value == "invalidated"


def test_hypothesis_lab_rejects_invalid_transition() -> None:
    engine = HypothesisLabEngine(InMemoryHypothesisLabStore())
    hyp = engine.create("firm-1", "case-1", "Hypothèse A")
    engine.archive("firm-1", hyp.id, actor="avocat-1")

    with pytest.raises(InvalidHypothesisTransitionError):
        engine.support("firm-1", hyp.id, actor="avocat-1")


def test_hypothesis_lab_get_unknown_raises_key_error() -> None:
    engine = HypothesisLabEngine(InMemoryHypothesisLabStore())

    with pytest.raises(KeyError):
        engine.get("firm-1", "unknown")
