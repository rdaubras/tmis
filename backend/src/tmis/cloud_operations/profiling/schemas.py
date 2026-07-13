import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ProfilingFindingType(StrEnum):
    """The four offender categories the sprint asks the profiler to
    identify ("fonctions lentes, requêtes coûteuses, appels IA
    excessifs, traitements bloquants")."""

    SLOW_FUNCTION = "slow_function"
    COSTLY_QUERY = "costly_query"
    EXCESSIVE_AI_CALLS = "excessive_ai_calls"
    BLOCKING_OPERATION = "blocking_operation"


_RECOMMENDATION_TEMPLATES: dict[ProfilingFindingType, str] = {
    ProfilingFindingType.SLOW_FUNCTION: "Consider caching or optimizing '{name}' (avg {avg:.1f}ms)",
    ProfilingFindingType.COSTLY_QUERY: "Add an index or reduce N+1 queries for '{name}'",
    ProfilingFindingType.EXCESSIVE_AI_CALLS: "Consider caching or batching AI calls for '{name}'",
    ProfilingFindingType.BLOCKING_OPERATION: "Consider making '{name}' asynchronous",
}


def new_profiling_sample_id() -> str:
    return f"prof-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class ProfilingSample:
    id: str
    finding_type: ProfilingFindingType
    name: str
    duration_ms: float
    firm_id: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class ProfilingRecommendation:
    finding_type: ProfilingFindingType
    name: str
    average_duration_ms: float
    occurrence_count: int
    recommendation: str
