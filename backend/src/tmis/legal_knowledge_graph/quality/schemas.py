from dataclasses import dataclass

from tmis.cabinet_knowledge.quality.schemas import QualityBreakdown


@dataclass(frozen=True, slots=True)
class GraphQualityBreakdown:
    """Extends `cabinet_knowledge.quality.QualityBreakdown` with the
    graph-specific signals the Sprint 25 Quality Engine asks for:
    doublons, incohérences, sources manquantes — never a second
    quality score computed from scratch."""

    node_id: str
    base_quality: QualityBreakdown | None
    duplicate_count: int
    contradiction_count: int
    missing_sources: bool
    confidence: float
