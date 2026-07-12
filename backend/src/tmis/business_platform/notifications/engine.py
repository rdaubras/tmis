from tmis.business_platform.notifications.schemas import BusinessNotificationType
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.collaboration.notifications.schemas import Notification, NotificationChannel


class BusinessNotificationEngine:
    """Composes `collaboration.notifications.NotificationEngine`
    (Sprint 8) rather than reimplementing dispatch/channel logic. That
    engine's `Notification.workspace_id` is just "the tenant scope
    this notification belongs to" — a firm id fits that slot exactly
    as well as a workspace id does, so a firm-scoped business
    notification is dispatched through the same engine with `firm_id`
    passed as `workspace_id`."""

    def __init__(self, notifications: NotificationEngine) -> None:
        self._notifications = notifications

    def notify(
        self,
        firm_id: str,
        recipient_id: str,
        notification_type: BusinessNotificationType,
        payload: dict[str, str],
        channels: list[NotificationChannel] | None = None,
    ) -> list[Notification]:
        return self._notifications.dispatch(
            workspace_id=firm_id,
            recipient_id=recipient_id,
            notification_type=notification_type.value,
            payload=payload,
            channels=channels or [NotificationChannel.IN_APP],
        )

    def list_for_firm(self, firm_id: str) -> list[Notification]:
        return self._notifications.list_for_workspace(firm_id)
