import uuid
from dataclasses import dataclass, field
from datetime import datetime


def new_report_id() -> str:
    return f"rpt-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class BusinessReport:
    """A structured, exportable snapshot of one firm's `analytics.
    BusinessDashboard` at a point in time — the raw dashboard is
    live/mutable; a report is the frozen, timestamped record a firm
    admin can archive or hand to `exports.ExportEngine`."""

    id: str
    firm_id: str
    generated_at: datetime
    sections: dict[str, str] = field(default_factory=dict)
