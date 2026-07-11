from typing import Any

import httpx


class HttpxTransport:
    """The production `HttpTransportPort` — thin wrapper over `httpx`
    (already a TMIS dependency, Sprint 2)."""

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self._base_url = base_url
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    async def request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self._base_url, headers=self._headers) as client:
            response = await client.request(method, path, json=json)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data


class InMemoryTransport:
    """A test double: records every call and returns a canned
    response registered via `stub()` — used by
    `tests/unit/platform_sdk` so the client SDK is tested without a
    real network call."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict[str, Any] | None]] = []
        self._responses: dict[tuple[str, str], dict[str, Any]] = {}

    def stub(self, method: str, path: str, response: dict[str, Any]) -> None:
        self._responses[(method, path)] = response

    async def request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self.calls.append((method, path, json))
        return self._responses.get((method, path), {})
