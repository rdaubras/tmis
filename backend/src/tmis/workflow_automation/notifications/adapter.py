from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.collaboration.notifications.schemas import Notification, NotificationChannel


class WorkflowNotificationAdapter:
    """Thin adapter reusing
    `collaboration.notifications.NotificationEngine` directly — same
    reuse convention as Sprint 16's `playbooks`/`review` adapters —
    rather than a second notification-dispatch implementation. A
    workflow's `firm_id` is passed through as the engine's
    `workspace_id`."""

    def __init__(self, notification_engine: NotificationEngine) -> None:
        self._notification_engine = notification_engine

    def notify(
        self,
        firm_id: str,
        recipient_id: str,
        notification_type: str,
        payload: dict[str, str],
        channels: list[NotificationChannel] | None = None,
    ) -> list[Notification]:
        return self._notification_engine.dispatch(
            firm_id,
            recipient_id,
            notification_type,
            payload,
            channels or [NotificationChannel.IN_APP],
        )
