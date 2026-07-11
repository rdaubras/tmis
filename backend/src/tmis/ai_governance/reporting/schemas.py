import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ReportType(StrEnum):
    """The sprint's explicit report catalog: rapport d'explicabilité,
    rapport de conformité, rapport d'audit IA, rapport des
    validations, rapport de qualité."""

    EXPLAINABILITY = "explainability"
    COMPLIANCE = "compliance"
    AI_AUDIT = "ai_audit"
    VALIDATIONS = "validations"
    QUALITY = "quality"


def new_report_id() -> str:
    return f"report-{uuid.uuid4()}"


@dataclass(frozen=True, slots=True)
class ReportSection:
    title: str
    content: str


@dataclass(frozen=True, slots=True)
class GovernanceReport:
    id: str
    type: ReportType
    firm_id: str
    production_id: str | None
    title: str
    sections: tuple[ReportSection, ...] = field(default_factory=tuple)
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
