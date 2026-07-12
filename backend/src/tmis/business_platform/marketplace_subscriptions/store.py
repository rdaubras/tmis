from tmis.business_platform.marketplace_subscriptions.schemas import ExtensionSubscription


class InMemoryExtensionSubscriptionStore:
    def __init__(self) -> None:
        self._subscriptions: dict[tuple[str, str], ExtensionSubscription] = {}

    def save(self, subscription: ExtensionSubscription) -> None:
        self._subscriptions[(subscription.firm_id, subscription.plugin_id)] = subscription

    def get(self, firm_id: str, plugin_id: str) -> ExtensionSubscription | None:
        return self._subscriptions.get((firm_id, plugin_id))

    def list_for_firm(self, firm_id: str) -> list[ExtensionSubscription]:
        return [s for (fid, _), s in self._subscriptions.items() if fid == firm_id]
