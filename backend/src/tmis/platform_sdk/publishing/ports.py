from typing import Protocol

from tmis.platform_sdk.publishing.schemas import PublishingEvent


class PublishingStorePort(Protocol):
    def append(self, event: PublishingEvent) -> None: ...

    def history(self, plugin_id: str) -> list[PublishingEvent]: ...
