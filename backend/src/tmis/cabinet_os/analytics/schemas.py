from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class FirmAnalytics:
    """Aggregate activity/productivity metrics for a firm (see
    docs/39-cabinet-os.md — Analytics Engine)."""

    firm_id: str
    client_count: int
    active_client_count: int
    document_count: int
    billable_minutes: int
    non_billable_minutes: int
    ai_requests: int
    average_minutes_per_case: float
    computed_at: datetime
