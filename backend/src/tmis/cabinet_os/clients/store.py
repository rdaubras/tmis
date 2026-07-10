from tmis.cabinet_os.clients.schemas import Client


class InMemoryClientStore:
    """Implements `ClientStorePort` with an in-memory dict."""

    def __init__(self) -> None:
        self._clients: dict[str, Client] = {}

    def get(self, client_id: str) -> Client | None:
        return self._clients.get(client_id)

    def save(self, client: Client) -> None:
        self._clients[client.id] = client

    def list_for_firm(self, firm_id: str) -> list[Client]:
        return [c for c in self._clients.values() if c.firm_id == firm_id]
