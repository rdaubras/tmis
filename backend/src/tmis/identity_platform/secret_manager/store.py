from tmis.identity_platform.secret_manager.schemas import ManagedSecret


class InMemoryManagedSecretStore:
    def __init__(self) -> None:
        self._secrets: dict[tuple[str, str], ManagedSecret] = {}

    def save(self, secret: ManagedSecret) -> None:
        self._secrets[(secret.firm_id, secret.key)] = secret

    def get(self, firm_id: str, key: str) -> ManagedSecret | None:
        return self._secrets.get((firm_id, key))

    def list_for_firm(self, firm_id: str) -> list[ManagedSecret]:
        return [s for s in self._secrets.values() if s.firm_id == firm_id]
