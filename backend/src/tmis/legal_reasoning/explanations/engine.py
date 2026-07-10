from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.confidence.schemas import ConfidenceScore
from tmis.legal_reasoning.conflicts.schemas import Conflict
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.explanations.schemas import Explanation
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis

_LOW_CONFIDENCE_THRESHOLD = 0.4


class ReasoningExplanationEngine:
    """Implements `ExplanationEnginePort`: assembles a plain-language
    trace of the reasoning run — steps followed, components involved,
    references mobilized, hypotheses considered, and the analysis'
    limitations — directly from the objects the orchestrator already
    produced, no extra computation (see docs/25-legal-reasoning.md —
    Explanations).
    """

    def build(
        self,
        question: str,
        hypotheses: list[Hypothesis],
        arguments: list[Argument],
        counter_arguments: list[CounterArgument],
        conflicts: list[Conflict],
        confidence_scores: dict[str, ConfidenceScore],
    ) -> Explanation:
        reasoning_steps = (
            f"Question posée : {question}",
            f"{len(hypotheses)} hypothèse(s) construite(s)",
            f"{len(arguments)} argument(s) rassemblé(s)",
            f"{len(counter_arguments)} contre-argument(s) identifié(s)",
            f"{len(conflicts)} conflit(s) détecté(s)",
        )
        components_used = (
            "hypotheses.HeuristicHypothesisEngine",
            "arguments.HeuristicArgumentEngine",
            "counter_arguments.HeuristicCounterArgumentEngine",
            "confidence.ConfigurableConfidenceEngine",
            "conflicts.HeuristicConflictDetector",
        )
        references = tuple(sorted({ref for h in hypotheses for ref in h.references}))
        hypotheses_considered = tuple(h.description for h in hypotheses)

        limitations = [
            "Cette analyse ne constitue pas un avis juridique et doit être "
            "validée par un avocat avant toute utilisation.",
        ]
        for hypothesis in hypotheses:
            score = confidence_scores.get(hypothesis.id)
            if score is not None and score.value < _LOW_CONFIDENCE_THRESHOLD:
                limitations.append(
                    f"Confiance faible pour « {hypothesis.description} » ({score.value:.2f})."
                )
        if conflicts:
            limitations.append(
                f"{len(conflicts)} conflit(s) non résolu(s) dans le dossier à examiner."
            )

        return Explanation(
            reasoning_steps=reasoning_steps,
            components_used=components_used,
            references=references,
            hypotheses_considered=hypotheses_considered,
            limitations=tuple(limitations),
        )
