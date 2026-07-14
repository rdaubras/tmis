from typing import Any

import httpx

from tmis.ai.connectors.adapters.piste_oauth import PisteOAuthTokenProvider
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError, ConnectorError
from tmis.ai.schemas.connector import ConnectorDocument


class JudilibreConnector:
    """Implements `ConnectorPort` for case law against the real Judilibre
    API (Cour de cassation), reached through the PISTE gateway — see
    `LegifranceConnector` for the shared OAuth mechanism and the same
    defensive-parsing rationale (docs/154-guide-configuration-connecteurs.md).
    """

    connector_name = "jurisprudence"

    def __init__(
        self,
        client: httpx.AsyncClient,
        token_provider: PisteOAuthTokenProvider,
        *,
        base_url: str,
    ) -> None:
        self._client = client
        self._token_provider = token_provider
        self._base_url = base_url.rstrip("/")

    async def _headers(self) -> dict[str, str]:
        token = await self._token_provider.get_token(self.connector_name)
        return {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async def search(
        self, query: str, filters: dict[str, object] | None = None
    ) -> list[ConnectorDocument]:
        headers = await self._headers()
        params: dict[str, str] = {"query": query, "page_size": "10"}
        payload = await self._get(f"{self._base_url}/search", params, headers)
        assert payload is not None  # noqa: S101 — allow_404 defaults to False here
        results = payload.get("results", []) if isinstance(payload, dict) else []

        documents: list[ConnectorDocument] = []
        for item in results:
            title = str(item.get("numero") or item.get("titre") or item.get("id", ""))
            documents.append(
                ConnectorDocument(
                    id=str(item.get("id", "")),
                    title=title,
                    content=str(item.get("summary") or item.get("text") or ""),
                    connector=self.connector_name,
                    metadata={
                        "jurisdiction": str(item.get("jurisdiction", "")),
                        "chamber": str(item.get("chamber", "")),
                        "decision_date": str(item.get("decision_date", "")),
                    },
                )
            )
        return documents

    async def fetch(self, document_id: str) -> ConnectorDocument | None:
        headers = await self._headers()
        payload = await self._get(
            f"{self._base_url}/decision", {"id": document_id}, headers, allow_404=True
        )
        if payload is None:
            return None
        return ConnectorDocument(
            id=document_id,
            title=str(payload.get("numero", document_id)),
            content=str(payload.get("text") or payload.get("summary") or ""),
            connector=self.connector_name,
            metadata={
                "jurisdiction": str(payload.get("jurisdiction", "")),
                "chamber": str(payload.get("chamber", "")),
                "decision_date": str(payload.get("decision_date", "")),
            },
        )

    async def _get(
        self,
        url: str,
        params: dict[str, str],
        headers: dict[str, str],
        *,
        allow_404: bool = False,
    ) -> dict[str, Any] | None:
        try:
            response = await self._client.get(url, params=params, headers=headers)
            if allow_404 and response.status_code == 404:
                return None
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401, 403):
                raise ConnectorAuthenticationError(self.connector_name, str(exc)) from exc
            raise ConnectorError(self.connector_name, str(exc)) from exc
        except httpx.HTTPError as exc:
            raise ConnectorError(self.connector_name, str(exc)) from exc
        result: dict[str, Any] = response.json()
        return result
