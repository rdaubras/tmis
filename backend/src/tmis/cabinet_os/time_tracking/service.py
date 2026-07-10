import uuid
from datetime import UTC, datetime, timedelta

from tmis.cabinet_os.time_tracking.ports import TimeEntryStorePort
from tmis.cabinet_os.time_tracking.schemas import ActivityType, EntryMethod, TimeEntry
from tmis.cabinet_os.time_tracking.store import InMemoryTimeEntryStore


class TimeTrackingService:
    """Implements `TimeTrackingEnginePort` (see docs/39-cabinet-os.md —
    Time Tracking Engine): manual logging, a live timer, and quick
    presets all produce the same `TimeEntry` shape."""

    def __init__(self, store: TimeEntryStorePort | None = None) -> None:
        self._store: TimeEntryStorePort = store or InMemoryTimeEntryStore()

    def log(
        self,
        firm_id: str,
        collaborator_id: str,
        case_id: str,
        duration_minutes: int,
        activity_type: ActivityType,
        *,
        comments: str = "",
        task_id: str | None = None,
        billable: bool = True,
    ) -> TimeEntry:
        now = datetime.now(UTC)
        entry = TimeEntry(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            collaborator_id=collaborator_id,
            case_id=case_id,
            activity_type=activity_type,
            entry_method=EntryMethod.MANUAL,
            started_at=now - timedelta(minutes=duration_minutes),
            ended_at=now,
            duration_minutes=duration_minutes,
            task_id=task_id,
            comments=comments,
            billable=billable,
            created_at=now,
        )
        self._store.save(entry)
        return entry

    def start_timer(
        self,
        firm_id: str,
        collaborator_id: str,
        case_id: str,
        activity_type: ActivityType,
        *,
        task_id: str | None = None,
    ) -> TimeEntry:
        now = datetime.now(UTC)
        entry = TimeEntry(
            id=str(uuid.uuid4()),
            firm_id=firm_id,
            collaborator_id=collaborator_id,
            case_id=case_id,
            activity_type=activity_type,
            entry_method=EntryMethod.TIMER,
            started_at=now,
            task_id=task_id,
            created_at=now,
        )
        self._store.save(entry)
        return entry

    def stop_timer(self, entry_id: str) -> TimeEntry:
        entry = self._store.get(entry_id)
        if entry is None:
            raise ValueError(f"Unknown time entry {entry_id!r}")
        if entry.ended_at is not None:
            raise ValueError(f"Time entry {entry_id!r} is not running")
        now = datetime.now(UTC)
        entry.ended_at = now
        entry.duration_minutes = max(0, round((now - entry.started_at).total_seconds() / 60))
        self._store.save(entry)
        return entry

    def total_minutes_for_case(self, case_id: str) -> int:
        return sum(e.duration_minutes or 0 for e in self._store.list_for_case(case_id))

    def list_for_collaborator(self, collaborator_id: str) -> list[TimeEntry]:
        return self._store.list_for_collaborator(collaborator_id)
