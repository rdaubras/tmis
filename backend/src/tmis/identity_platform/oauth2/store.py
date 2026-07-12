from tmis.identity_platform.oauth2.schemas import AuthorizationCodeRecord, OAuth2Client


class InMemoryOAuth2ClientStore:
    def __init__(self) -> None:
        self._clients: dict[str, OAuth2Client] = {}

    def save(self, client: OAuth2Client) -> None:
        self._clients[client.client_id] = client

    def get(self, client_id: str) -> OAuth2Client | None:
        return self._clients.get(client_id)


class InMemoryAuthorizationCodeStore:
    def __init__(self) -> None:
        self._codes: dict[str, AuthorizationCodeRecord] = {}

    def save(self, record: AuthorizationCodeRecord) -> None:
        self._codes[record.code] = record

    def get(self, code: str) -> AuthorizationCodeRecord | None:
        return self._codes.get(code)
