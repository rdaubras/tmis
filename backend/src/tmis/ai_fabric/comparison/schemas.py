from dataclasses import dataclass, field

from tmis.ai_fabric.evaluation.schemas import ResponseMetrics


@dataclass(frozen=True, slots=True)
class ComparisonEntry:
    model_name: str
    metrics: ResponseMetrics
    coverage_score: float
    prompt_compliance_score: float
    overall_score: float


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    prompt: str
    entries: tuple[ComparisonEntry, ...] = field(default_factory=tuple)

    @property
    def ranked_model_names(self) -> tuple[str, ...]:
        return tuple(
            entry.model_name
            for entry in sorted(self.entries, key=lambda e: e.overall_score, reverse=True)
        )
