import uuid
from datetime import UTC, datetime

from tmis.collaboration.notifications.channels import EmailChannel, InAppChannel, WebhookChannel
from tmis.collaboration.notifications.ports import NotificationChannelPort
from tmis.collaboration.notifications.schemas import Notification, NotificationChannel

_DEFAULT_CHANNELS: dict[NotificationChannel, NotificationChannelPort] = {
    NotificationChannel.IN_APP: InAppChannel(),
    NotificationChannel.EMAIL: EmailChannel(),
    NotificationChannel.WEBHOOK: WebhookChannel(),
}


class NotificationEngine:
    """Implements `NotificationEnginePort`: extensible over channels —
    register a new `NotificationChannelPort` for a
    `NotificationChannel` (or an entirely new channel value) without
    touching this class (see docs/37-guide-notifications.md)."""

    def __init__(
        self,
        channels: dict[NotificationChannel, NotificationChannelPort] | None = None,
    ) -> None:
        self._channels: dict[NotificationChannel, NotificationChannelPort] = (
            channels if channels is not None else dict(_DEFAULT_CHANNELS)
        )
        self._notifications: dict[str, Notification] = {}

    def dispatch(
        self,
        workspace_id: str,
        recipient_id: str,
        notification_type: str,
        payload: dict[str, str],
        channels: list[NotificationChannel],
    ) -> list[Notification]:
        created: list[Notification] = []
        for channel in channels:
            notification = Notification(
                id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                recipient_id=recipient_id,
                channel=channel,
                type=notification_type,
                payload=dict(payload),
                created_at=datetime.now(UTC),
            )
            self._notifications[notification.id] = notification
            channel_impl = self._channels.get(channel)
            if channel_impl is not None:
                channel_impl.send(notification)
            created.append(notification)
        return created

    def mark_read(self, notification_id: str) -> Notification:
        notification = self._notifications.get(notification_id)
        if notification is None:
            raise ValueError(f"Unknown notification {notification_id!r}")
        notification.read_at = datetime.now(UTC)
        return notification

    def list_for_recipient(self, recipient_id: str) -> list[Notification]:
        return [n for n in self._notifications.values() if n.recipient_id == recipient_id]

    def list_for_workspace(self, workspace_id: str) -> list[Notification]:
        return [n for n in self._notifications.values() if n.workspace_id == workspace_id]
