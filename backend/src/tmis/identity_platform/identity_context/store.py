from tmis.identity_platform.identity_context.schemas import IdentityContext


class InMemoryIdentityContextStore:
    def __init__(self) -> None:
        self._contexts: dict[tuple[str, str], IdentityContext] = {}

    def save(self, context: IdentityContext) -> None:
        self._contexts[(context.firm_id, context.user_id)] = context

    def get(self, firm_id: str, user_id: str) -> IdentityContext | None:
        return self._contexts.get((firm_id, user_id))
