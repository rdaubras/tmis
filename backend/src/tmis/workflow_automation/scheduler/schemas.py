import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta


def new_scheduled_trigger_id() -> str:
    return f"sched-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class ScheduledTrigger:
    """A `SCHEDULE`/`DEADLINE`-typed trigger's next firing time.
    `interval` is `None` for a one-shot trigger (e.g. a fixed hearing
    date) or set for a recurring one (e.g. "every Monday at 9am")."""

    id: str
    firm_id: str
    workflow_id: str
    trigger_id: str
    next_fire_at: datetime
    interval: timedelta | None = None
