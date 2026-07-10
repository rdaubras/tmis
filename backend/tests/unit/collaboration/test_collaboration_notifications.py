import pytest

from tmis.collaboration.notifications.channels import EmailChannel, WebhookChannel
from tmis.collaboration.notifications.engine import NotificationEngine
from tmis.collaboration.notifications.schemas import NotificationChannel


def test_dispatch_creates_one_notification_per_channel() -> None:
    engine = NotificationEngine()
    created = engine.dispatch(
        "ws-1", "member-1", "task_assigned", {"task_id": "t1"},
        [NotificationChannel.IN_APP, NotificationChannel.EMAIL],
    )

    assert len(created) == 2
    assert {n.channel for n in created} == {NotificationChannel.IN_APP, NotificationChannel.EMAIL}


def test_email_channel_records_what_would_be_sent_without_sending() -> None:
    email_channel = EmailChannel()
    engine = NotificationEngine({NotificationChannel.EMAIL: email_channel})

    engine.dispatch("ws-1", "member-1", "mention", {}, [NotificationChannel.EMAIL])

    assert len(email_channel.sent) == 1
    assert email_channel.sent[0].recipient_id == "member-1"


def test_webhook_channel_records_what_would_be_posted() -> None:
    webhook_channel = WebhookChannel()
    engine = NotificationEngine({NotificationChannel.WEBHOOK: webhook_channel})

    engine.dispatch("ws-1", "member-1", "approval_decided", {}, [NotificationChannel.WEBHOOK])

    assert len(webhook_channel.sent) == 1


def test_mark_read_sets_read_at() -> None:
    engine = NotificationEngine()
    [notification] = engine.dispatch(
        "ws-1", "member-1", "mention", {}, [NotificationChannel.IN_APP]
    )
    assert notification.read_at is None

    marked = engine.mark_read(notification.id)

    assert marked.read_at is not None


def test_mark_read_unknown_notification_raises() -> None:
    engine = NotificationEngine()

    with pytest.raises(ValueError, match="Unknown notification"):
        engine.mark_read("nope")


def test_list_for_recipient_filters_by_recipient() -> None:
    engine = NotificationEngine()
    engine.dispatch("ws-1", "member-1", "mention", {}, [NotificationChannel.IN_APP])
    engine.dispatch("ws-1", "member-2", "mention", {}, [NotificationChannel.IN_APP])

    inbox = engine.list_for_recipient("member-1")

    assert len(inbox) == 1
    assert inbox[0].recipient_id == "member-1"


def test_list_for_workspace_filters_by_workspace() -> None:
    engine = NotificationEngine()
    engine.dispatch("ws-1", "member-1", "mention", {}, [NotificationChannel.IN_APP])
    engine.dispatch("ws-2", "member-1", "mention", {}, [NotificationChannel.IN_APP])

    for_ws1 = engine.list_for_workspace("ws-1")

    assert len(for_ws1) == 1
    assert for_ws1[0].workspace_id == "ws-1"
