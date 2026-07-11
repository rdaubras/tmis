from typing import Any, Protocol


class HttpTransportPort(Protocol):
    """The only thing a `TmisApiClient` depends on — deliberately a
    single `request()` method so any language can implement the same
    contract against TMIS's public REST API (see the sprint's "PUBLIC
    API SDK" spec: "prévoir une architecture permettant des SDK dans
    plusieurs langages"). The Python client here is the reference
    implementation; a TypeScript client would define an equivalent
    interface calling the same OpenAPI-documented endpoints."""

    async def request(
        self, method: str, path: str, json: dict[str, Any] | None = None
    ) -> dict[str, Any]: ...
