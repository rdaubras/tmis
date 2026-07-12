from typing import Protocol

from tmis.integration_hub.scheduler.schemas import ScheduledSync


class SyncSchedulerStorePort(Protocol):
    def add(self, scheduled: ScheduledSync) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[ScheduledSync]: ...
