from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.confidence.schemas import ConfidenceScore
from tmis.legal_reasoning.conflicts.schemas import Conflict, ConflictType
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_reasoning.strategy.engine import HeuristicStrategyEngine


def test_propose_returns_one_option_per_hypothesis() -> None:
    h1 = Hypothesis(id="h1", description="d1")
    h2 = Hypothesis(id="h2", description="d2")

    options = HeuristicStrategyEngine().propose([h1, h2], [], [], [], {})

    assert {o.hypothesis_id for o in options} == {"h1", "h2"}


def test_favorable_points_come_from_matching_arguments() -> None:
    hypothesis = Hypothesis(id="h1", description="d1")
    argument = Argument(
        id="a1", hypothesis_id="h1", claim="Argument favorable",
        source_connector="codes", source_reference="ref", excerpt="e",
    )

    options = HeuristicStrategyEngine().propose([hypothesis], [argument], [], [], {})

    assert options[0].favorable_points == ("Argument favorable",)


def test_risks_include_counter_arguments_and_conflicts() -> None:
    hypothesis = Hypothesis(id="h1", description="d1", supporting_fact_ids=("f1",))
    argument = Argument(
        id="a1", hypothesis_id="h1", claim="claim",
        source_connector="codes", source_reference="ref", excerpt="e",
    )
    counter = CounterArgument(
        id="c1", argument_id="a1", claim="Contre-argument",
        source_connector="doctrine", source_reference="ref2", excerpt="e2",
    )
    conflict = Conflict(
        id="conf1", type=ConflictType.FACT_INCONSISTENCY,
        description="Conflit sur f1", explanation="expl", involved_ids=("f1",),
    )

    options = HeuristicStrategyEngine().propose([hypothesis], [argument], [counter], [conflict], {})

    assert "Contre-argument" in options[0].risks
    assert "Conflit sur f1" in options[0].risks


def test_missing_elements_flag_low_confidence() -> None:
    hypothesis = Hypothesis(id="h1", description="d1")
    scores = {"h1": ConfidenceScore(hypothesis_id="h1", value=0.1, explanation="low")}

    options = HeuristicStrategyEngine().propose([hypothesis], [], [], [], scores)

    assert any("Confiance encore faible" in m for m in options[0].missing_elements)


def test_missing_elements_flag_absence_of_arguments() -> None:
    hypothesis = Hypothesis(id="h1", description="d1")
    options = HeuristicStrategyEngine().propose([hypothesis], [], [], [], {})
    assert any("Aucun argument" in m for m in options[0].missing_elements)


def test_never_picks_a_single_winner() -> None:
    h1 = Hypothesis(id="h1", description="d1")
    h2 = Hypothesis(id="h2", description="d2")
    options = HeuristicStrategyEngine().propose([h1, h2], [], [], [], {})
    assert len(options) == 2
