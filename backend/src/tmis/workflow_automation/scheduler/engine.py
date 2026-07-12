from datetime import datetime, timedelta

from tmis.workflow_automation.scheduler.ports import SchedulerStorePort
from tmis.workflow_automation.scheduler.schemas import ScheduledTrigger, new_scheduled_trigger_id


class SchedulerEngine:
    """Fires `SCHEDULE`/`DEADLINE` triggers by time rather than by
    event — polled via `due()` (there is no background loop in this
    sprint; a future scheduler process calls `due()` periodically and
    `mark_fired()` after dispatching)."""

    def __init__(self, store: SchedulerStorePort) -> None:
        self._store = store

    def schedule(
        self,
        firm_id: str,
        workflow_id: str,
        trigger_id: str,
        next_fire_at: datetime,
        interval: timedelta | None = None,
    ) -> ScheduledTrigger:
        scheduled = ScheduledTrigger(
            id=new_scheduled_trigger_id(),
            firm_id=firm_id,
            workflow_id=workflow_id,
            trigger_id=trigger_id,
            next_fire_at=next_fire_at,
            interval=interval,
        )
        self._store.add(scheduled)
        return scheduled

    def due(self, firm_id: str, now: datetime) -> list[ScheduledTrigger]:
        return [s for s in self._store.list_for_firm(firm_id) if s.next_fire_at <= now]

    def mark_fired(self, scheduled: ScheduledTrigger, now: datetime) -> ScheduledTrigger:
        if scheduled.interval is not None:
            scheduled.next_fire_at = now + scheduled.interval
        return scheduled
