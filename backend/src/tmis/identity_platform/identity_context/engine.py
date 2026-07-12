from tmis.identity_platform.identity_context.ports import IdentityContextStorePort
from tmis.identity_platform.identity_context.schemas import IdentityContext


class IdentityContextEngine:
    def __init__(self, store: IdentityContextStorePort) -> None:
        self._store = store

    def set_context(self, context: IdentityContext) -> IdentityContext:
        self._store.save(context)
        return context

    def get_context(self, firm_id: str, user_id: str) -> IdentityContext | None:
        return self._store.get(firm_id, user_id)

    def get_or_default(self, firm_id: str, user_id: str) -> IdentityContext:
        context = self._store.get(firm_id, user_id)
        if context is None:
            context = IdentityContext(user_id=user_id, firm_id=firm_id)
            self._store.save(context)
        return context
