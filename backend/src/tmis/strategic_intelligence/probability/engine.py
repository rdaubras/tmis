from tmis.strategic_intelligence.probability.schemas import Likelihood, ProbabilityAssessment


class ProbabilityEngine:
    """Assesses the likelihood of a strategy *sub-element* — never the
    case as a whole. `supporting_count`/`contradicting_count` are
    pre-computed by the caller (e.g. from `evidence_gap` or
    `case_intelligence.facts`), keeping this engine free of cross-
    context imports."""

    def assess(
        self,
        element_description: str,
        *,
        supporting_count: int,
        contradicting_count: int,
    ) -> ProbabilityAssessment:
        total = supporting_count + contradicting_count
        if total == 0:
            likelihood = Likelihood.MEDIUM
            rationale = (
                f"Aucun élément corroborant ou contredisant « {element_description} » "
                "n'est disponible : estimation neutre par défaut."
            )
        else:
            ratio = supporting_count / total
            if ratio >= 0.66:
                likelihood = Likelihood.HIGH
            elif ratio <= 0.33:
                likelihood = Likelihood.LOW
            else:
                likelihood = Likelihood.MEDIUM
            rationale = (
                f"{supporting_count} élément(s) corroborant(s) contre "
                f"{contradicting_count} contredisant(s) pour « {element_description} »."
            )
        return ProbabilityAssessment(
            element_description=element_description,
            likelihood=likelihood,
            rationale=rationale,
        )
