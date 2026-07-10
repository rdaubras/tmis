from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass(slots=True)
class Notification:
    """One notification sent through one channel (see
    docs/37-guide-notifications.md). A single logical event dispatched
    to three channels produces three `Notification` records — each
    channel's delivery is tracked independently."""

    id: str
    workspace_id: str
    recipient_id: str
    channel: NotificationChannel
    type: str
    payload: dict[str, str] = field(default_factory=dict)
    created_at: datetime | None = None
    read_at: datetime | None = None
