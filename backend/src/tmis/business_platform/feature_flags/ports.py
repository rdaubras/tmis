from typing import Protocol

from tmis.business_platform.feature_flags.schemas import BusinessFlagExtras


class BusinessFlagExtrasStorePort(Protocol):
    def save(self, extras: BusinessFlagExtras) -> None: ...

    def get(self, key: str) -> BusinessFlagExtras | None: ...

    def list_all(self) -> list[BusinessFlagExtras]: ...
