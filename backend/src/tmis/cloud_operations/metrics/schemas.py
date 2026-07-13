import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class MetricCategory(StrEnum):
    """The ten measurement categories the sprint asks for
    ("temps de réponse, temps des appels IA, consommation mémoire,
    CPU, files d'attente, cache, base de données, nombre de
    workflows, erreurs, débit")."""

    RESPONSE_TIME = "response_time"
    AI_CALL_DURATION = "ai_call_duration"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    QUEUE_DEPTH = "queue_depth"
    CACHE = "cache"
    DATABASE = "database"
    WORKFLOW_COUNT = "workflow_count"
    ERRORS = "errors"
    THROUGHPUT = "throughput"
    # Added in Sprint 24 (Legal Copilot Framework) — same additive
    # pattern as Sprint 22: new categories on the same MetricsEngine,
    # never a second metrics store.
    COPILOT_USAGE = "copilot_usage"
    AI_COST = "ai_cost"
    VALIDATION_RATE = "validation_rate"
    PACK_REUSE = "pack_reuse"
    SATISFACTION = "satisfaction"


class MetricKind(StrEnum):
    """Which `platform.metrics` primitive a category maps to — see
    `engine._KIND_FOR_CATEGORY`."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


def new_metric_event_id() -> str:
    return f"met-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class MetricEvent:
    """One historized observation. `platform.metrics.MetricsRegistry`
    (Sprint 10) only holds current aggregate state — a `Counter` has
    no memory of *when* it was incremented. This event is what makes
    every metric "historisée" (sprint requirement): an append-only log
    time-series queries can replay, alongside the live registry that
    still backs the Prometheus `/metrics` endpoint."""

    id: str
    category: MetricCategory
    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    firm_id: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
