from typing import Protocol

from tmis.integration_hub.webhooks.schemas import WebhookDeliveryResult, WebhookSubscription


class WebhookSubscriptionStorePort(Protocol):
    def save(self, subscription: WebhookSubscription) -> None: ...

    def get(self, firm_id: str, subscription_id: str) -> WebhookSubscription | None: ...

    def list_for_connector(self, firm_id: str, connector_id: str) -> list[WebhookSubscription]: ...


class WebhookSenderPort(Protocol):
    """Decoupled input — the actual HTTP transport (httpx, aiohttp...)
    is supplied by the caller so `WebhookEngine` never hard-depends on
    a specific client library."""

    async def send(
        self, url: str, payload: dict[str, str], headers: dict[str, str]
    ) -> WebhookDeliveryResult: ...
