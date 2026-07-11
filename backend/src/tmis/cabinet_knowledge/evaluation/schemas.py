from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class KnowledgeBaseEvaluation:
    firm_id: str
    total_objects: int
    by_status: dict[str, int]
    validation_rate: float
    average_quality_score: float
    most_reused: tuple[str, ...]
    feedback_acceptance_rate: float
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
