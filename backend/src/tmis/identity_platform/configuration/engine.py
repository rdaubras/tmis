from tmis.identity_platform.authentication.schemas import AuthMethod
from tmis.identity_platform.configuration.ports import IdentityConfigurationStorePort
from tmis.identity_platform.configuration.schemas import IdentityConfiguration


class IdentityConfigurationEngine:
    def __init__(self, store: IdentityConfigurationStorePort) -> None:
        self._store = store

    def get_or_default(self, firm_id: str) -> IdentityConfiguration:
        configuration = self._store.get(firm_id)
        if configuration is None:
            configuration = IdentityConfiguration(firm_id=firm_id)
            self._store.save(configuration)
        return configuration

    def set_allowed_auth_methods(
        self, firm_id: str, methods: frozenset[AuthMethod]
    ) -> IdentityConfiguration:
        configuration = self.get_or_default(firm_id)
        configuration.allowed_auth_methods = methods
        self._store.save(configuration)
        return configuration

    def set_mfa_required(self, firm_id: str, required: bool) -> IdentityConfiguration:
        configuration = self.get_or_default(firm_id)
        configuration.mfa_required = required
        self._store.save(configuration)
        return configuration

    def set_session_ttl_hours(self, firm_id: str, hours: int) -> IdentityConfiguration:
        configuration = self.get_or_default(firm_id)
        configuration.session_ttl_hours = hours
        self._store.save(configuration)
        return configuration

    def is_auth_method_allowed(self, firm_id: str, method: AuthMethod) -> bool:
        return method in self.get_or_default(firm_id).allowed_auth_methods
