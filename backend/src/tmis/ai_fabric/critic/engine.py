from tmis.ai_fabric.critic.schemas import CriticVerdict
from tmis.ai_fabric.evaluation.engine import ResponseEvaluator

_CONTRADICTION_PENALTY = 0.15


class CriticModel:
    """The sprint's "CRITIC MODEL": "ne génère jamais. Il évalue
    uniquement" — checks coherence, citations, contradictions, and
    quality of a response already produced by another model. Built on
    `tmis.ai_fabric.evaluation.ResponseEvaluator` rather than calling
    any provider itself, so a critique never introduces new content."""

    def __init__(self, evaluator: ResponseEvaluator | None = None) -> None:
        self._evaluator = evaluator or ResponseEvaluator()

    def review(self, model_name: str, response_text: str) -> CriticVerdict:
        metrics = self._evaluator.evaluate(response_text)
        issues: list[str] = list(metrics.contradiction_flags)
        if metrics.citation_count == 0:
            issues.append("aucune citation ou référence détectée")

        quality_score = max(
            0.0,
            metrics.coherence_score
            - _CONTRADICTION_PENALTY * len(metrics.contradiction_flags),
        )

        return CriticVerdict(
            model_name=model_name,
            metrics=metrics,
            quality_score=quality_score,
            issues=tuple(issues),
        )
