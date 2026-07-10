from dataclasses import dataclass, field
from enum import Enum


class ReportFormat(str, Enum):
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    HTML = "html"


@dataclass(frozen=True, slots=True)
class ReportTable:
    """A generic tabular report — any `cabinet_os` engine can produce
    one (dashboards, analytics, billing, time tracking...) without the
    Report Engine knowing what it represents (see
    docs/43-guide-rapports.md)."""

    title: str
    headers: list[str]
    rows: list[list[str]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ReportResult:
    format: ReportFormat
    filename: str
    content: bytes
    media_type: str
