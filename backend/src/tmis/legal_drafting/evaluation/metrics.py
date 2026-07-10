from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DraftMetrics:
    """Metrics for one drafting run (see docs/28-legal-drafting.md —
    Observabilité): generation duration, components used, paragraph and
    reference counts, estimated cost, and the exact template version
    used."""

    document_id: str
    duration_ms: float
    components_used: tuple[str, ...]
    paragraph_count: int
    reference_count: int
    estimated_cost_usd: float
    template_id: str
