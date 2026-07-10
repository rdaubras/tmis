import uuid

from tmis.legal_reasoning.arguments.schemas import Argument
from tmis.legal_reasoning.confidence.schemas import ConfidenceScore
from tmis.legal_reasoning.conflicts.schemas import Conflict
from tmis.legal_reasoning.counter_arguments.schemas import CounterArgument
from tmis.legal_reasoning.hypotheses.schemas import Hypothesis
from tmis.legal_reasoning.strategy.schemas import StrategyOption

_LOW_CONFIDENCE_THRESHOLD = 0.4


class HeuristicStrategyEngine:
    """Implements `StrategyEnginePort`: proposes one `StrategyOption` per
    hypothesis, deriving favorable points from its arguments, risks from
    its counter-arguments and any conflict touching its supporting facts,
    and missing elements from a low confidence score (see
    docs/25-legal-reasoning.md — Strategy Engine). It never ranks or
    picks a winner among the options it returns.
    """

    def propose(
        self,
        hypotheses: list[Hypothesis],
        arguments: list[Argument],
        counter_arguments: list[CounterArgument],
        conflicts: list[Conflict],
        confidence_scores: dict[str, ConfidenceScore],
    ) -> list[StrategyOption]:
        options: list[StrategyOption] = []
        for hypothesis in hypotheses:
            hyp_arguments = [a for a in arguments if a.hypothesis_id == hypothesis.id]
            hyp_argument_ids = {a.id for a in hyp_arguments}
            hyp_counters = [c for c in counter_arguments if c.argument_id in hyp_argument_ids]
            conflicting = [
                c for c in conflicts if set(c.involved_ids) & set(hypothesis.supporting_fact_ids)
            ]

            missing_elements: list[str] = []
            score = confidence_scores.get(hypothesis.id)
            if score is not None and score.value < _LOW_CONFIDENCE_THRESHOLD:
                missing_elements.append(
                    f"Confiance encore faible ({score.value:.2f}) — rechercher des "
                    "éléments complémentaires."
                )
            if not hyp_arguments:
                missing_elements.append("Aucun argument documentaire trouvé pour cette hypothèse.")

            options.append(
                StrategyOption(
                    id=str(uuid.uuid4()),
                    hypothesis_id=hypothesis.id,
                    objective=f"Étayer l'hypothèse : {hypothesis.description}",
                    favorable_points=tuple(a.claim for a in hyp_arguments),
                    risks=tuple(c.claim for c in hyp_counters)
                    + tuple(c.description for c in conflicting),
                    missing_elements=tuple(missing_elements),
                )
            )
        return options
