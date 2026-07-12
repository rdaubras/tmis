from typing import Protocol


class UsedMagicLinkStorePort(Protocol):
    def is_used(self, token: str) -> bool: ...

    def mark_used(self, token: str) -> None: ...
