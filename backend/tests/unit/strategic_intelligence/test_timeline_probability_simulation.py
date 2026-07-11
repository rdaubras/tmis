from tmis.strategic_intelligence.probability.engine import ProbabilityEngine
from tmis.strategic_intelligence.probability.schemas import Likelihood
from tmis.strategic_intelligence.simulation.engine import SimulationEngine
from tmis.strategic_intelligence.timeline.engine import TimelineEngine
from tmis.strategic_intelligence.timeline.schemas import StrategicTimelineEntry, TimelineEntryKind


def test_timeline_engine_sorts_entries_by_date() -> None:
    engine = TimelineEngine()
    entries = [
        StrategicTimelineEntry("2026-03-01", TimelineEntryKind.DEADLINE, "Saisine CPH", "ref-1"),
        StrategicTimelineEntry("2026-01-15", TimelineEntryKind.FACT, "Licenciement", "ref-2"),
        StrategicTimelineEntry(
            "2026-02-01", TimelineEntryKind.PROPOSED_ACTION, "Mise en demeure", "ref-3"
        ),
    ]

    sorted_entries = engine.build(entries)

    assert [e.date for e in sorted_entries] == ["2026-01-15", "2026-02-01", "2026-03-01"]


def test_probability_engine_high_likelihood_when_mostly_supporting() -> None:
    engine = ProbabilityEngine()

    assessment = engine.assess("Admissibilité", supporting_count=8, contradicting_count=1)

    assert assessment.likelihood is Likelihood.HIGH
    assert assessment.rationale


def test_probability_engine_low_likelihood_when_mostly_contradicting() -> None:
    engine = ProbabilityEngine()

    assessment = engine.assess("Admissibilité", supporting_count=1, contradicting_count=8)

    assert assessment.likelihood is Likelihood.LOW


def test_probability_engine_neutral_with_no_data() -> None:
    engine = ProbabilityEngine()

    assessment = engine.assess("Admissibilité", supporting_count=0, contradicting_count=0)

    assert assessment.likelihood is Likelihood.MEDIUM


def test_probability_assessment_never_scopes_to_case_outcome() -> None:
    engine = ProbabilityEngine()

    assessment = engine.assess(
        "Recevabilité du témoignage", supporting_count=1, contradicting_count=1
    )

    assert not hasattr(assessment, "win_probability")
    assert not hasattr(assessment, "outcome")


def test_simulation_engine_flags_affected_strategies_by_keyword() -> None:
    engine = SimulationEngine()

    result = engine.run(
        "case-1",
        {
            "strategy-1": "Fondée sur le témoignage du collègue",
            "strategy-2": "Stratégie procédurale sans lien",
        },
        ("témoignage",),
    )

    assert result.affected_strategy_ids == ("strategy-1",)
    assert result.notes


def test_simulation_engine_never_predicts_an_outcome() -> None:
    engine = SimulationEngine()

    result = engine.run("case-1", {"strategy-1": "text"}, ("text",))

    assert not hasattr(result, "win_probability")
    assert not hasattr(result, "prediction")


def test_simulation_engine_no_matches_yields_empty_result() -> None:
    engine = SimulationEngine()

    result = engine.run("case-1", {"strategy-1": "rien à voir"}, ("mot-clé-absent",))

    assert result.affected_strategy_ids == ()
    assert result.notes == ()
