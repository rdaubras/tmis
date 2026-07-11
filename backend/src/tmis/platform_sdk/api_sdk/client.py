from typing import Any

from tmis.platform_sdk.api_sdk.ports import HttpTransportPort


class TmisApiClient:
    """The sprint's "PUBLIC API SDK" — the official Python client
    library. A handful of typed convenience methods demonstrate the
    pattern; any other public endpoint (see docs/44-guide-api-
    publique.md, Sprint 9) is reachable through the generic
    `request()` escape hatch."""

    def __init__(self, transport: HttpTransportPort) -> None:
        self._transport = transport

    async def request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self._transport.request(method, path, json=json)

    async def list_marketplace_plugins(self, query: str | None = None) -> dict[str, Any]:
        params = f"?query={query}" if query else ""
        return await self._transport.request("GET", f"/api/v1/platform-sdk/marketplace{params}")

    async def install_plugin(
        self, firm_id: str, plugin_id: str, permissions: list[str]
    ) -> dict[str, Any]:
        return await self._transport.request(
            "POST",
            f"/api/v1/platform-sdk/marketplace/{plugin_id}/install",
            json={"firm_id": firm_id, "permissions": permissions},
        )

    async def search_knowledge(self, firm_id: str, keyword: str) -> dict[str, Any]:
        return await self._transport.request(
            "POST",
            "/api/v1/cabinet-knowledge/search",
            json={"firm_id": firm_id, "keyword": keyword},
        )
