from typing import Any

import httpx

from tmis.ai.connectors.exceptions import ConnectorAuthenticationError, ConnectorError
from tmis.ai.schemas.connector import ConnectorDocument


class HttpConnector:
    """Implements `ConnectorPort` against any HTTP+JSON document source
    that exposes a `GET {base_url}{search_path}?q=...` search endpoint and
    a `GET {base_url}{document_path}` fetch-by-id endpoint — the "generic
    HTTP connector, configurable" fallback for sources with no
    domain-specific public API (doctrine) and for sources that are
    firm-specific by nature (internal documentation, a licensed private
    database), each wired independently rather than hardcoded (see
    docs/154-guide-configuration-connecteurs.md).
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        connector_name: str,
        base_url: str,
        api_key: str | None = None,
        search_path: str = "/search",
        document_path: str = "/documents/{id}",
    ) -> None:
        self.connector_name = connector_name
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._search_path = search_path
        self._document_path = document_path

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def search(
        self, query: str, filters: dict[str, object] | None = None
    ) -> list[ConnectorDocument]:
        params: dict[str, str] = {"q": query}
        params.update({key: str(value) for key, value in (filters or {}).items()})
        response = await self._get(f"{self._base_url}{self._search_path}", params)
        assert response is not None  # noqa: S101 — allow_404 defaults to False here
        payload = response.json()
        items = payload.get("results", []) if isinstance(payload, dict) else payload
        return [self._to_document(item) for item in items]

    async def fetch(self, document_id: str) -> ConnectorDocument | None:
        path = self._document_path.format(id=document_id)
        response = await self._get(f"{self._base_url}{path}", allow_404=True)
        if response is None:
            return None
        return self._to_document(response.json())

    async def _get(
        self, url: str, params: dict[str, str] | None = None, *, allow_404: bool = False
    ) -> httpx.Response | None:
        try:
            response = await self._client.get(url, params=params, headers=self._headers())
            if allow_404 and response.status_code == 404:
                return None
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                raise ConnectorAuthenticationError(self.connector_name, str(exc)) from exc
            raise ConnectorError(self.connector_name, str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ConnectorError(self.connector_name, str(exc)) from exc
        return response

    def _to_document(self, item: dict[str, Any]) -> ConnectorDocument:
        raw_metadata = item.get("metadata") or {}
        return ConnectorDocument(
            id=str(item.get("id", "")),
            title=str(item.get("title", "")),
            content=str(item.get("content", "")),
            connector=self.connector_name,
            metadata={str(key): str(value) for key, value in dict(raw_metadata).items()},
        )
