from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class StageMetric:
    """Timing/outcome of a single pipeline stage, for one document."""

    stage: str
    duration_ms: float
    success: bool
    error: str | None = None


@dataclass(frozen=True, slots=True)
class PipelineMetrics:
    """Aggregated metrics for one full pipeline run (see
    docs/14-document-intelligence.md — Observabilité)."""

    document_id: str
    total_duration_ms: float
    stage_metrics: tuple[StageMetric, ...] = field(default_factory=tuple)
    ocr_confidence: float | None = None
    entity_count: int = 0
    chunk_count: int = 0
    knowledge_node_count: int = 0

    @property
    def error_count(self) -> int:
        return sum(1 for stage in self.stage_metrics if not stage.success)
