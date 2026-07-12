from tmis.integration_hub.webhooks.schemas import WebhookSubscription


class InMemoryWebhookSubscriptionStore:
    def __init__(self) -> None:
        self._subscriptions: dict[str, WebhookSubscription] = {}

    def save(self, subscription: WebhookSubscription) -> None:
        self._subscriptions[subscription.id] = subscription

    def get(self, firm_id: str, subscription_id: str) -> WebhookSubscription | None:
        sub = self._subscriptions.get(subscription_id)
        if sub is None or sub.firm_id != firm_id:
            return None
        return sub

    def list_for_connector(self, firm_id: str, connector_id: str) -> list[WebhookSubscription]:
        return [
            s
            for s in self._subscriptions.values()
            if s.firm_id == firm_id and s.connector_id == connector_id
        ]
