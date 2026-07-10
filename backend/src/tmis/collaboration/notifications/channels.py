from tmis.collaboration.notifications.schemas import Notification


class InAppChannel:
    """Implements `NotificationChannelPort`: stores nothing itself — the
    `Notification` is already persisted by `NotificationEngine` before a
    channel is asked to send it, so the in-app channel only needs to be
    a no-op marker that the notification is visible in-app immediately.
    """

    def send(self, notification: Notification) -> None:
        return None


class EmailChannel:
    """Implements `NotificationChannelPort` as an interface/stub (see
    docs/37-guide-notifications.md): records what *would* be emailed,
    without sending anything — real SMTP/provider wiring is future
    work behind this same port."""

    def __init__(self) -> None:
        self.sent: list[Notification] = []

    def send(self, notification: Notification) -> None:
        self.sent.append(notification)


class WebhookChannel:
    """Implements `NotificationChannelPort` as an interface/stub: records
    what *would* be POSTed to a configured webhook URL, without making
    any HTTP call — real delivery is future work behind this same port.
    """

    def __init__(self) -> None:
        self.sent: list[Notification] = []

    def send(self, notification: Notification) -> None:
        self.sent.append(notification)
