from tmis.cabinet_os.public_api.schemas import ApiKey, OAuthClient, OAuthToken


class InMemoryApiKeyStore:
    def __init__(self) -> None:
        self._keys: dict[str, ApiKey] = {}

    def get(self, key_id: str) -> ApiKey | None:
        return self._keys.get(key_id)

    def get_by_hash(self, key_hash: str) -> ApiKey | None:
        return next((k for k in self._keys.values() if k.key_hash == key_hash), None)

    def save(self, key: ApiKey) -> None:
        self._keys[key.id] = key

    def list_for_firm(self, firm_id: str) -> list[ApiKey]:
        return [k for k in self._keys.values() if k.firm_id == firm_id]


class InMemoryOAuthClientStore:
    def __init__(self) -> None:
        self._clients: dict[str, OAuthClient] = {}

    def get_by_client_id(self, client_id: str) -> OAuthClient | None:
        return self._clients.get(client_id)

    def save(self, client: OAuthClient) -> None:
        self._clients[client.client_id] = client


class InMemoryOAuthTokenStore:
    def __init__(self) -> None:
        self._tokens: dict[str, OAuthToken] = {}

    def save(self, token: OAuthToken) -> None:
        self._tokens[token.token] = token

    def get(self, token: str) -> OAuthToken | None:
        return self._tokens.get(token)
