import uuid

import pytest

from tmis.ai.events.bus import EventBus
from tmis.ai.events.events import UserQuestionReceived, WorkflowStarted


@pytest.mark.asyncio
async def test_publish_calls_subscribed_handler() -> None:
    bus = EventBus()
    received: list[UserQuestionReceived] = []

    async def handler(event: UserQuestionReceived) -> None:
        received.append(event)

    bus.subscribe(UserQuestionReceived, handler)
    event = UserQuestionReceived(workflow_id=uuid.uuid4(), question="Bonjour ?")
    await bus.publish(event)

    assert received == [event]


@pytest.mark.asyncio
async def test_publish_does_not_call_handlers_of_other_event_types() -> None:
    bus = EventBus()
    calls = []

    async def handler(event: WorkflowStarted) -> None:
        calls.append(event)

    bus.subscribe(WorkflowStarted, handler)
    await bus.publish(UserQuestionReceived(workflow_id=uuid.uuid4(), question="?"))

    assert calls == []


@pytest.mark.asyncio
async def test_unsubscribe_stops_delivery() -> None:
    bus = EventBus()
    calls = []

    async def handler(event: UserQuestionReceived) -> None:
        calls.append(event)

    bus.subscribe(UserQuestionReceived, handler)
    bus.unsubscribe(UserQuestionReceived, handler)
    await bus.publish(UserQuestionReceived(workflow_id=uuid.uuid4(), question="?"))

    assert calls == []


@pytest.mark.asyncio
async def test_history_records_every_published_event() -> None:
    bus = EventBus()
    event = UserQuestionReceived(workflow_id=uuid.uuid4(), question="?")
    await bus.publish(event)

    assert bus.history == [event]
