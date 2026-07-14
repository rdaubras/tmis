from typing import Any

import httpx

from tmis.ai.connectors.adapters.piste_oauth import PisteOAuthTokenProvider
from tmis.ai.connectors.exceptions import ConnectorAuthenticationError, ConnectorError
from tmis.ai.schemas.connector import ConnectorDocument


class LegifranceConnector:
    """Implements `ConnectorPort` for legal codes and statutory texts
    against the real Légifrance API (DILA), reached through the PISTE
    gateway (see docs/154-guide-configuration-connecteurs.md).

    Endpoint paths and request/response shapes follow the publicly
    documented Légifrance API on `api.gouv.fr`/`piste.gouv.fr`; both the
    base URL and every field read from the response are treated
    defensively (`.get()` with fallbacks) so a minor schema drift on the
    DILA side degrades gracefully instead of raising, and an operator can
    repoint `base_url` via config without a code change if DILA moves an
    endpoint.
    """

    connector_name = "codes"

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
        body = {
            "recherche": {
                "champs": [
                    {
                        "typeChamp": "ALL",
                        "criteres": [
                            {"typeRecherche": "UN_DES_MOTS", "valeur": query, "operateur": "ET"}
                        ],
                        "operateur": "ET",
                    }
                ],
                "pageNumber": 1,
                "pageSize": 10,
                "sort": "PERTINENCE",
                "typePagination": "DEFAUT",
            },
            "fond": "CODE_DATE",
        }
        payload = await self._post(f"{self._base_url}/search", body, headers)
        assert payload is not None  # noqa: S101 — allow_404 defaults to False here
        results = payload.get("results", []) if isinstance(payload, dict) else []

        documents: list[ConnectorDocument] = []
        for item in results:
            titre = str(item.get("titre") or item.get("title") or "")
            extracts = item.get("extracts") or []
            content = (
                " ".join(str(extract["values"][0]) for extract in extracts if extract.get("values"))
                or titre
            )
            documents.append(
                ConnectorDocument(
                    id=str(item.get("id") or titre),
                    title=titre,
                    content=content,
                    connector=self.connector_name,
                    metadata={
                        "nature": str(item.get("nature", "")),
                        "date": str(item.get("date", "")),
                    },
                )
            )
        return documents

    async def fetch(self, document_id: str) -> ConnectorDocument | None:
        headers = await self._headers()
        payload = await self._post(
            f"{self._base_url}/consult/getArticle", {"id": document_id}, headers, allow_404=True
        )
        if payload is None:
            return None
        return ConnectorDocument(
            id=document_id,
            title=str(payload.get("title", document_id)),
            content=str(payload.get("texte") or payload.get("content") or ""),
            connector=self.connector_name,
            metadata={"nature": str(payload.get("nature", ""))},
        )

    async def _post(
        self,
        url: str,
        body: dict[str, Any],
        headers: dict[str, str],
        *,
        allow_404: bool = False,
    ) -> dict[str, Any] | None:
        try:
            response = await self._client.post(url, json=body, headers=headers)
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
