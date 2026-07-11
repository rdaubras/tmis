from tmis.ai_fabric.comparison.schemas import ComparisonEntry, ComparisonResult
from tmis.ai_fabric.evaluation.engine import ResponseEvaluator, jaccard_similarity

_COHERENCE_WEIGHT = 0.4
_COVERAGE_WEIGHT = 0.3
_COMPLIANCE_WEIGHT = 0.2
_CITATION_WEIGHT = 0.1


class ComparisonEngine:
    """The sprint's "COMPARISON ENGINE": compares several models'
    answers to the *same* prompt on coherence, references, length,
    coverage, and prompt-compliance, and ranks them — never picks a
    single "winner" to discard the rest, that synthesis role belongs
    to `tmis.ai_fabric.consensus` and `tmis.ai_fabric.fusion`."""

    def __init__(self, evaluator: ResponseEvaluator | None = None) -> None:
        self._evaluator = evaluator or ResponseEvaluator()

    def compare(self, prompt: str, responses: dict[str, str]) -> ComparisonResult:
        entries: list[ComparisonEntry] = []
        for model_name, response_text in responses.items():
            metrics = self._evaluator.evaluate(response_text)
            coverage_score = jaccard_similarity(prompt, response_text)
            prompt_compliance_score = coverage_score
            citation_bonus = 1.0 if metrics.citation_count > 0 else 0.0
            overall_score = (
                _COHERENCE_WEIGHT * metrics.coherence_score
                + _COVERAGE_WEIGHT * coverage_score
                + _COMPLIANCE_WEIGHT * prompt_compliance_score
                + _CITATION_WEIGHT * citation_bonus
            )
            entries.append(
                ComparisonEntry(
                    model_name=model_name,
                    metrics=metrics,
                    coverage_score=coverage_score,
                    prompt_compliance_score=prompt_compliance_score,
                    overall_score=overall_score,
                )
            )
        return ComparisonResult(prompt=prompt, entries=tuple(entries))
