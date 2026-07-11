from typing import Protocol

from tmis.workflow_automation.scheduler.schemas import ScheduledTrigger


class SchedulerStorePort(Protocol):
    def add(self, scheduled: ScheduledTrigger) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[ScheduledTrigger]: ...
