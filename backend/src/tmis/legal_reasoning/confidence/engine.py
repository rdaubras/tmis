from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.confidence.schemas import ConfidenceScore, ConfidenceWeights
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.evidence.schemas import ReasoningEvidenceLink
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis

_MAX_ARGUMENTS_FOR_FULL_SUPPORT = 3


class ConfigurableConfidenceEngine:
    """Implements `ConfidenceEnginePort`: combines three factors — how
    many arguments support the hypothesis, how reliable its evidence is,
    and how few counter-arguments were found against it — into a single
    weighted, explained score (see docs/27-guide-scores-confiance.md).
    """

    def score(
        self,
        hypothesis: Hypothesis,
        arguments: list[Argument],
        counter_arguments: list[CounterArgument],
        evidence_links: list[ReasoningEvidenceLink],
        weights: ConfidenceWeights | None = None,
    ) -> ConfidenceScore:
        effective_weights = (weights or ConfidenceWeights()).normalized()

        hyp_arguments = [a for a in arguments if a.hypothesis_id == hypothesis.id]
        hyp_argument_ids = {a.id for a in hyp_arguments}
        hyp_counters = [c for c in counter_arguments if c.argument_id in hyp_argument_ids]
        hyp_evidence = [e for e in evidence_links if e.hypothesis_id == hypothesis.id]

        argument_support = min(1.0, len(hyp_arguments) / _MAX_ARGUMENTS_FOR_FULL_SUPPORT)
        evidence_reliability = (
            sum(e.reliability_score for e in hyp_evidence) / len(hyp_evidence)
            if hyp_evidence
            else 0.0
        )
        # A hypothesis with no arguments at all has nothing for a
        # counter-argument to attach to — the absence of counter-arguments
        # is not a positive signal in that case, it's simply undefined, so
        # it must not inflate the score of a wholly unsupported hypothesis.
        if not hyp_arguments:
            absence_of_counter_arguments = 0.0
        elif not hyp_counters:
            absence_of_counter_arguments = 1.0
        else:
            absence_of_counter_arguments = max(0.0, 1.0 - len(hyp_counters) / len(hyp_arguments))

        value = (
            effective_weights.argument_support * argument_support
            + effective_weights.evidence_reliability * evidence_reliability
            + effective_weights.absence_of_counter_arguments * absence_of_counter_arguments
        )

        explanation = (
            f"{len(hyp_arguments)} argument(s) favorable(s), fiabilité moyenne des preuves "
            f"{evidence_reliability:.2f}, {len(hyp_counters)} contre-argument(s) recensé(s)."
        )
        return ConfidenceScore(
            hypothesis_id=hypothesis.id,
            value=value,
            explanation=explanation,
            factors={
                "argument_support": argument_support,
                "evidence_reliability": evidence_reliability,
                "absence_of_counter_arguments": absence_of_counter_arguments,
            },
        )
