from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CabinetDashboard:
    """Firm-level dashboard (see docs/39-cabinet-os.md — Dashboard
    Engine): revenue, open dossiers, hearings, billable time, AI
    activity."""

    firm_id: str
    revenue: float
    open_case_count: int
    hearing_count: int
    billable_minutes: int
    ai_requests: int
    computed_at: datetime


@dataclass(frozen=True, slots=True)
class CollaboratorDashboard:
    """Per-collaborator dashboard: tasks, dossiers, deadlines, time."""

    collaborator_id: str
    task_count: int
    open_task_count: int
    case_count: int
    upcoming_deadline_count: int
    tracked_minutes: int
    computed_at: datetime


@dataclass(frozen=True, slots=True)
class AdminDashboard:
    """Administrator dashboard: licences, storage, AI consumption."""

    firm_id: str
    plan: str
    active_users: int
    max_users: int
    storage_gb_used: float
    max_storage_gb: float
    ai_requests_used: int
    max_ai_requests_per_month: int
    computed_at: datetime
