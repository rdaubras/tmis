from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.confidence.engine import ConfigurableConfidenceEngine
from tmis.legal_reasoning.confidence.schemas import ConfidenceWeights
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis


def _argument(argument_id: str, hypothesis_id: str) -> Argument:
    return Argument(
        id=argument_id,
        hypothesis_id=hypothesis_id,
        claim="claim",
        source_connector="codes",
        source_reference="ref",
        excerpt="excerpt",
    )


def test_score_is_zero_with_no_support_at_all() -> None:
    hypothesis = Hypothesis(id="h1", description="desc")
    score = ConfigurableConfidenceEngine().score(hypothesis, [], [], [])
    assert score.value == 0.0


def test_score_increases_with_more_arguments() -> None:
    hypothesis = Hypothesis(id="h1", description="desc")
    one_argument = [_argument("a1", "h1")]
    three_arguments = [_argument("a1", "h1"), _argument("a2", "h1"), _argument("a3", "h1")]

    low = ConfigurableConfidenceEngine().score(hypothesis, one_argument, [], [])
    high = ConfigurableConfidenceEngine().score(hypothesis, three_arguments, [], [])

    assert high.value > low.value


def test_score_decreases_with_counter_arguments() -> None:
    hypothesis = Hypothesis(id="h1", description="desc")
    arguments = [_argument("a1", "h1")]
    counters = [
        CounterArgument(
            id="c1",
            argument_id="a1",
            claim="c",
            source_connector="doctrine",
            source_reference="ref",
            excerpt="e",
        )
    ]

    without_counter = ConfigurableConfidenceEngine().score(hypothesis, arguments, [], [])
    with_counter = ConfigurableConfidenceEngine().score(hypothesis, arguments, counters, [])

    assert with_counter.value < without_counter.value


def test_score_uses_evidence_reliability() -> None:
    hypothesis = Hypothesis(id="h1", description="desc")
    evidence = [
        ReasoningEvidenceLink(
            id="e1", fact_id="f1", document_id="d1", hypothesis_id="h1", argument_id=None,
            reliability_score=0.9,
        )
    ]
    score = ConfigurableConfidenceEngine().score(hypothesis, [], [], evidence)
    assert score.factors["evidence_reliability"] == 0.9


def test_score_explanation_mentions_counts() -> None:
    hypothesis = Hypothesis(id="h1", description="desc")
    arguments = [_argument("a1", "h1")]
    score = ConfigurableConfidenceEngine().score(hypothesis, arguments, [], [])
    assert "1 argument" in score.explanation


def test_weights_are_normalized_even_if_caller_passes_arbitrary_values() -> None:
    hypothesis = Hypothesis(id="h1", description="desc")
    arguments = [_argument("a1", "h1"), _argument("a2", "h1"), _argument("a3", "h1")]
    weights = ConfidenceWeights(
        argument_support=10.0, evidence_reliability=0.0, absence_of_counter_arguments=0.0
    )

    score = ConfigurableConfidenceEngine().score(hypothesis, arguments, [], [], weights)

    assert score.value == 1.0
