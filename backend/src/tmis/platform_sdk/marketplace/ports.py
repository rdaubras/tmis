from typing import Protocol

from tmis.platform_sdk.marketplace.schemas import Review


class ReviewStorePort(Protocol):
    def save(self, review: Review) -> None: ...

    def list_for_plugin(self, plugin_id: str) -> list[Review]: ...
