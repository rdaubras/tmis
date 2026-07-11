from dataclasses import dataclass, field

from tmis.ai_fabric.evaluation.schemas import ResponseMetrics


@dataclass(frozen=True, slots=True)
class CriticVerdict:
    model_name: str
    metrics: ResponseMetrics
    quality_score: float
    issues: tuple[str, ...] = field(default_factory=tuple)
