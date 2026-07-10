from typing import Protocol

from tmis.collaboration.notifications.schemas import Notification, NotificationChannel


class NotificationChannelPort(Protocol):
    """Port implemented by every interchangeable delivery channel."""

    def send(self, notification: Notification) -> None: ...


class NotificationEnginePort(Protocol):
    """Port implemented by every interchangeable notification engine."""

    def dispatch(
        self,
        workspace_id: str,
        recipient_id: str,
        notification_type: str,
        payload: dict[str, str],
        channels: list[NotificationChannel],
    ) -> list[Notification]: ...

    def mark_read(self, notification_id: str) -> Notification: ...

    def list_for_recipient(self, recipient_id: str) -> list[Notification]: ...

    def list_for_workspace(self, workspace_id: str) -> list[Notification]: ...
