from typing import Protocol

from tmis.identity_platform.identity_context.schemas import IdentityContext


class IdentityContextStorePort(Protocol):
    def save(self, context: IdentityContext) -> None: ...

    def get(self, firm_id: str, user_id: str) -> IdentityContext | None: ...
