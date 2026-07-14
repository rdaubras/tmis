from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphAnalyticsSnapshot:
    """The Sprint 25 Phase 10 metrics: connaissances les plus
    utilisées (via `graph_size`/`enrichments`), recherches sans
    résultat, domaines sous-documentés is left to a firm's own
    dashboard query over `relevant_knowledge`/`identified_risks` —
    this snapshot covers the five directly quantifiable ones."""

    node_count: float
    avg_search_latency_ms: float
    unresolved_search_count: int
    human_validation_count: int
    enrichment_count: int
    avg_answer_quality: float
