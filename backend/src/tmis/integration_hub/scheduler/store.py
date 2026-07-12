from tmis.integration_hub.scheduler.schemas import ScheduledSync


class InMemorySyncSchedulerStore:
    def __init__(self) -> None:
        self._scheduled: dict[tuple[str, str], ScheduledSync] = {}

    def add(self, scheduled: ScheduledSync) -> None:
        self._scheduled[(scheduled.firm_id, scheduled.id)] = scheduled

    def list_for_firm(self, firm_id: str) -> list[ScheduledSync]:
        return [s for (fid, _), s in self._scheduled.items() if fid == firm_id]
