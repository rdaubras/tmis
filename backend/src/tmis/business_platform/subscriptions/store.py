from tmis.business_platform.subscriptions.schemas import Subscription


class InMemorySubscriptionStore:
    def __init__(self) -> None:
        self._subscriptions: dict[str, Subscription] = {}

    def save(self, subscription: Subscription) -> None:
        self._subscriptions[subscription.firm_id] = subscription

    def get(self, firm_id: str) -> Subscription | None:
        return self._subscriptions.get(firm_id)

    def list_all(self) -> list[Subscription]:
        return list(self._subscriptions.values())
