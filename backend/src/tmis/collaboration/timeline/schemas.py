from dataclasses import dataclass
from datetime import datetime

from tmis.collaboration.activity.schemas import ActivityType


@dataclass(frozen=True, slots=True)
class TimelineEntry:
    """One chronological point in a target's (dossier, document, task...)
    history — a read-model projection of an `ActivityEntry`, not a
    separately stored fact (see docs/33-legal-collaboration.md —
    Timeline)."""

    activity_type: ActivityType
    actor_id: str
    summary: str
    occurred_at: datetime
