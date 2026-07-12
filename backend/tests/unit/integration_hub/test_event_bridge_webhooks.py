import hashlib
import hmac
import json

import pytest

from tmis.integration_hub.event_bridge import (
    EventBridge,
    EventDirection,
    ExternalRecordChanged,
    IntegrationEventBus,
)
from tmis.integration_hub.webhooks import (
    InMemoryWebhookSubscriptionStore,
    WebhookDeliveryResult,
    WebhookEngine,
    WebhookSubscription,
    sign_payload,
    verify_signature,
)
from tmis.workflow_automation.event_bus import IntegrationEventReceived, WorkflowEventBus


def test_sign_and_verify_payload_roundtrip() -> None:
    body = b'{"a": 1}'
    signature = sign_payload("secret", body)
    assert verify_signature("secret", body, signature)
    assert not verify_signature("secret", body, "wrong")


@pytest.mark.asyncio
async def test_integration_event_bus_publish_subscribe() -> None:
    bus = IntegrationEventBus()
    received = []

    async def handler(event: ExternalRecordChanged) -> None:
        received.append(event)

    bus.subscribe(ExternalRecordChanged, handler)
    event = ExternalRecordChanged(
        firm_id="f1", connector_id="c1", direction=EventDirection.INBOUND,
        entity_type="client", external_id="e1",
    )
    await bus.publish(event)
    assert received == [event]
    assert bus.history == [event]


@pytest.mark.asyncio
async def test_event_bridge_forwards_to_workflow_bus() -> None:
    workflow_bus = WorkflowEventBus()
    received = []

    async def handler(event: IntegrationEventReceived) -> None:
        received.append(event)

    workflow_bus.subscribe(IntegrationEventReceived, handler)
    integration_bus = IntegrationEventBus()
    EventBridge(integration_bus, workflow_bus)

    await integration_bus.publish(
        ExternalRecordChanged(
            firm_id="f1", connector_id="c1", direction=EventDirection.INBOUND,
            entity_type="client", external_id="e1", payload={"name": "x"},
        )
    )

    assert len(received) == 1
    assert received[0].integration_name == "c1"
    assert received[0].label == "client"
    assert received[0].payload == {"name": "x"}


@pytest.mark.asyncio
async def test_event_bridge_no_workflow_bus_is_noop() -> None:
    integration_bus = IntegrationEventBus()
    EventBridge(integration_bus, None)
    await integration_bus.publish(
        ExternalRecordChanged(
            firm_id="f1", connector_id="c1", direction=EventDirection.INBOUND,
            entity_type="client", external_id="e1",
        )
    )


class _FakeSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, dict[str, str], dict[str, str]]] = []

    async def send(
        self, url: str, payload: dict[str, str], headers: dict[str, str]
    ) -> WebhookDeliveryResult:
        self.sent.append((url, payload, headers))
        return WebhookDeliveryResult(success=True, status_code=200)


@pytest.mark.asyncio
async def test_webhook_engine_dispatch_outbound_filters_by_event_type() -> None:
    store = InMemoryWebhookSubscriptionStore()
    store.save(
        WebhookSubscription(
            id="w1", connector_id="c1", firm_id="f1", url="https://ext/hook",
            direction=EventDirection.OUTBOUND, secret="s", event_types=("client.updated",),
        )
    )
    store.save(
        WebhookSubscription(
            id="w2", connector_id="c1", firm_id="f1", url="https://ext/other",
            direction=EventDirection.OUTBOUND, secret="s", event_types=("client.deleted",),
        )
    )
    sender = _FakeSender()
    engine = WebhookEngine(store, sender)

    results = await engine.dispatch_outbound("f1", "c1", "client.updated", {"name": "x"})
    assert len(results) == 1
    assert results[0].success
    assert len(sender.sent) == 1
    assert sender.sent[0][0] == "https://ext/hook"


@pytest.mark.asyncio
async def test_webhook_engine_receive_inbound_valid_signature_publishes_event() -> None:
    store = InMemoryWebhookSubscriptionStore()
    subscription = WebhookSubscription(
        id="w1", connector_id="c1", firm_id="f1", url="https://ext/hook",
        direction=EventDirection.INBOUND, secret="shh",
    )
    store.save(subscription)

    integration_bus = IntegrationEventBus()
    engine = WebhookEngine(store, _FakeSender(), integration_bus)

    body = json.dumps(
        {"entity_type": "client", "external_id": "e1", "payload": {"name": "x"}}, sort_keys=True
    ).encode()
    signature = hmac.new(b"shh", body, hashlib.sha256).hexdigest()

    ok = await engine.receive_inbound(subscription, body, signature, "client", "e1", {"name": "x"})
    assert ok is True
    assert len(integration_bus.history) == 1


@pytest.mark.asyncio
async def test_webhook_engine_receive_inbound_invalid_signature_rejected() -> None:
    store = InMemoryWebhookSubscriptionStore()
    subscription = WebhookSubscription(
        id="w1", connector_id="c1", firm_id="f1", url="https://ext/hook",
        direction=EventDirection.INBOUND, secret="shh",
    )
    store.save(subscription)
    integration_bus = IntegrationEventBus()
    engine = WebhookEngine(store, _FakeSender(), integration_bus)

    ok = await engine.receive_inbound(subscription, b"body", "wrong-sig", "client", "e1", {})
    assert ok is False
    assert integration_bus.history == []
