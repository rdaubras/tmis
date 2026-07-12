import json

from tmis.integration_hub.event_bridge.bus import IntegrationEventBus
from tmis.integration_hub.event_bridge.schemas import EventDirection, ExternalRecordChanged
from tmis.integration_hub.webhooks.ports import WebhookSenderPort, WebhookSubscriptionStorePort
from tmis.integration_hub.webhooks.schemas import WebhookDeliveryResult, WebhookSubscription
from tmis.integration_hub.webhooks.signing import sign_payload, verify_signature


class WebhookEngine:
    """Outbound dispatch (TMIS -> external system) and inbound
    verification (external system -> TMIS), both HMAC-signed —
    "toutes les communications avec des systèmes externes doivent
    être ... signées et journalisées" (sprint requirement). A verified
    inbound delivery is re-published on `IntegrationEventBus` as an
    `ExternalRecordChanged`, which `EventBridge` then forwards into
    `workflow_automation`."""

    def __init__(
        self,
        store: WebhookSubscriptionStorePort,
        sender: WebhookSenderPort,
        event_bus: IntegrationEventBus | None = None,
    ) -> None:
        self._store = store
        self._sender = sender
        self._event_bus = event_bus

    async def dispatch_outbound(
        self, firm_id: str, connector_id: str, event_type: str, payload: dict[str, str]
    ) -> list[WebhookDeliveryResult]:
        subscriptions = [
            s
            for s in self._store.list_for_connector(firm_id, connector_id)
            if s.enabled
            and s.direction is EventDirection.OUTBOUND
            and (not s.event_types or event_type in s.event_types)
        ]
        body = json.dumps(payload, sort_keys=True).encode()
        results = []
        for subscription in subscriptions:
            signature = sign_payload(subscription.secret, body)
            result = await self._sender.send(
                subscription.url, payload, {"X-TMIS-Signature": signature}
            )
            results.append(result)
        return results

    def verify_inbound(
        self, subscription: WebhookSubscription, raw_body: bytes, signature: str
    ) -> bool:
        return verify_signature(subscription.secret, raw_body, signature)

    async def receive_inbound(
        self,
        subscription: WebhookSubscription,
        raw_body: bytes,
        signature: str,
        entity_type: str,
        external_id: str,
        payload: dict[str, str],
    ) -> bool:
        if not self.verify_inbound(subscription, raw_body, signature):
            return False
        if self._event_bus is not None:
            await self._event_bus.publish(
                ExternalRecordChanged(
                    firm_id=subscription.firm_id,
                    connector_id=subscription.connector_id,
                    direction=EventDirection.INBOUND,
                    entity_type=entity_type,
                    external_id=external_id,
                    payload=payload,
                )
            )
        return True
