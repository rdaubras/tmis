from tmis.identity_platform.configuration.schemas import IdentityConfiguration


class InMemoryIdentityConfigurationStore:
    def __init__(self) -> None:
        self._configurations: dict[str, IdentityConfiguration] = {}

    def save(self, configuration: IdentityConfiguration) -> None:
        self._configurations[configuration.firm_id] = configuration

    def get(self, firm_id: str) -> IdentityConfiguration | None:
        return self._configurations.get(firm_id)
