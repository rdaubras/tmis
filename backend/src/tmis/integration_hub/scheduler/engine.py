from datetime import datetime, timedelta

from tmis.integration_hub.scheduler.ports import SyncSchedulerStorePort
from tmis.integration_hub.scheduler.schemas import ScheduledSync, new_scheduled_sync_id


class SyncSchedulerEngine:
    """Fires sync jobs by time — polled via `due()` (no background
    loop in this sprint; a future scheduler process calls `due()`
    periodically and `mark_fired()` after dispatching each job to the
    `queue`). Same shape as
    `workflow_automation.scheduler.SchedulerEngine`, reimplemented
    locally since the LIH is a distinct bounded context."""

    def __init__(self, store: SyncSchedulerStorePort) -> None:
        self._store = store

    def schedule(
        self,
        firm_id: str,
        job_id: str,
        next_fire_at: datetime,
        interval: timedelta | None = None,
    ) -> ScheduledSync:
        scheduled = ScheduledSync(
            id=new_scheduled_sync_id(),
            firm_id=firm_id,
            job_id=job_id,
            next_fire_at=next_fire_at,
            interval=interval,
        )
        self._store.add(scheduled)
        return scheduled

    def due(self, firm_id: str, now: datetime) -> list[ScheduledSync]:
        return [s for s in self._store.list_for_firm(firm_id) if s.next_fire_at <= now]

    def mark_fired(self, scheduled: ScheduledSync, now: datetime) -> ScheduledSync:
        if scheduled.interval is not None:
            scheduled.next_fire_at = now + scheduled.interval
        return scheduled
