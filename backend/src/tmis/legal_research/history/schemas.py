from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ResearchHistoryEntry:
    """One recorded research run — user, case, query, date, connectors
    used, duration, results (see docs/21-legal-research.md — History)."""

    id: str
    query_text: str
    timestamp: datetime
    connectors_used: tuple[str, ...]
    duration_ms: float
    result_count: int
    user_id: str | None = None
    case_id: str | None = None
