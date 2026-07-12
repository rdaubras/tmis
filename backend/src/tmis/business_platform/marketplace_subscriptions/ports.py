from typing import Protocol

from tmis.business_platform.marketplace_subscriptions.schemas import ExtensionSubscription


class ExtensionSubscriptionStorePort(Protocol):
    def save(self, subscription: ExtensionSubscription) -> None: ...

    def get(self, firm_id: str, plugin_id: str) -> ExtensionSubscription | None: ...

    def list_for_firm(self, firm_id: str) -> list[ExtensionSubscription]: ...
