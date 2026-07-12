import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta


def new_scheduled_sync_id() -> str:
    return f"schedsync-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class ScheduledSync:
    """One sync job's next firing time. `interval` is `None` for a
    one-shot run or set for a recurring schedule (e.g. every 15
    minutes) — "toutes les synchronisations sont configurables"
    (sprint requirement)."""

    id: str
    firm_id: str
    job_id: str
    next_fire_at: datetime
    interval: timedelta | None = None
