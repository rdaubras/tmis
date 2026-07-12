from typing import Protocol

from tmis.business_platform.subscriptions.schemas import Subscription


class SubscriptionStorePort(Protocol):
    def save(self, subscription: Subscription) -> None: ...

    def get(self, firm_id: str) -> Subscription | None: ...

    def list_all(self) -> list[Subscription]: ...
