from typing import Protocol

from tmis.cabinet_os.time_tracking.schemas import ActivityType, TimeEntry


class TimeEntryStorePort(Protocol):
    def get(self, entry_id: str) -> TimeEntry | None: ...

    def save(self, entry: TimeEntry) -> None: ...

    def list_for_case(self, case_id: str) -> list[TimeEntry]: ...

    def list_for_collaborator(self, collaborator_id: str) -> list[TimeEntry]: ...

    def list_for_firm(self, firm_id: str) -> list[TimeEntry]: ...


class TimeTrackingEnginePort(Protocol):
    """Port implemented by every interchangeable time tracking engine."""

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
    ) -> TimeEntry: ...

    def start_timer(
        self,
        firm_id: str,
        collaborator_id: str,
        case_id: str,
        activity_type: ActivityType,
        *,
        task_id: str | None = None,
    ) -> TimeEntry: ...

    def stop_timer(self, entry_id: str) -> TimeEntry: ...

    def total_minutes_for_case(self, case_id: str) -> int: ...

    def list_for_collaborator(self, collaborator_id: str) -> list[TimeEntry]: ...
