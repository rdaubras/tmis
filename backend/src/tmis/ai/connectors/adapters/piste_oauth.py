import time

import httpx

from tmis.ai.connectors.exceptions import ConnectorAuthenticationError, ConnectorError


class PisteOAuthTokenProvider:
    """Caches an OAuth2 client-credentials access token for the PISTE
    gateway (`oauth.piste.gouv.fr`), which fronts both Légifrance and
    Judilibre — shared by `LegifranceConnector` and `JudilibreConnector`
    so a token is fetched once per expiry window rather than once per
    request."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str = "openid",
    ) -> None:
        self._client = client
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._token: str | None = None
        self._expires_at: float = 0.0

    async def get_token(self, connector_name: str) -> str:
        if self._token is not None and time.monotonic() < self._expires_at:
            return self._token

        try:
            response = await self._client.post(
                self._token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": self._scope,
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                raise ConnectorAuthenticationError(
                    connector_name, f"PISTE OAuth token request rejected: {exc}"
                ) from exc
            raise ConnectorError(
                connector_name, f"PISTE OAuth token request failed: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ConnectorError(
                connector_name, f"PISTE OAuth token request failed: {exc}"
            ) from exc

        payload = response.json()
        token = payload["access_token"]
        ttl_seconds = float(payload.get("expires_in", 3600))
        self._token = token
        self._expires_at = time.monotonic() + max(ttl_seconds - 30.0, 0.0)
        return str(token)
