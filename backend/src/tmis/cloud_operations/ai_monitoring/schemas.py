import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class AIQualityIssueKind(StrEnum):
    HALLUCINATION = "hallucination"
    BIAS = "bias"


def new_ai_quality_incident_id() -> str:
    return f"aiq-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class AIQualityIncident:
    """One historized finding from `ai_governance.hallucination_
    detection`/`.bias_detection` — those engines only ever return an
    in-memory `list[...]` for a single scan; this is what makes a
    finding queryable over time ("hallucinations détectées" as a
    monitoring metric, sprint requirement)."""

    id: str
    kind: AIQualityIssueKind
    excerpt: str
    detail: str
    firm_id: str | None = None
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
