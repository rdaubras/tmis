from dataclasses import dataclass
from enum import StrEnum


class OptimizationCategory(StrEnum):
    """The six analysis dimensions the sprint asks for ("temps CPU,
    consommation mémoire, contention, appels IA, temps Workflow,
    latence API")."""

    CPU = "cpu"
    MEMORY = "memory"
    CONTENTION = "contention"
    AI_CALLS = "ai_calls"
    WORKFLOW = "workflow"
    API_LATENCY = "api_latency"


class OptimizationSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class OptimizationRecommendation:
    category: OptimizationCategory
    severity: OptimizationSeverity
    metric_value: float
    description: str
