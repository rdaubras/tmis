from tmis.workflow_automation.scheduler.schemas import ScheduledTrigger


class InMemorySchedulerStore:
    def __init__(self) -> None:
        self._scheduled: dict[tuple[str, str], ScheduledTrigger] = {}

    def add(self, scheduled: ScheduledTrigger) -> None:
        self._scheduled[(scheduled.firm_id, scheduled.id)] = scheduled

    def list_for_firm(self, firm_id: str) -> list[ScheduledTrigger]:
        return [s for (fid, _), s in self._scheduled.items() if fid == firm_id]
