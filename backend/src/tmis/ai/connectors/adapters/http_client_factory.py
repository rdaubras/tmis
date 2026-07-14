from functools import lru_cache

import httpx


@lru_cache
def get_connector_http_client() -> httpx.AsyncClient:
    """Process-wide `httpx.AsyncClient` singleton shared by every real
    connector adapter (Légifrance, Judilibre, the generic `HttpConnector`)
    — one connection pool instead of one per connector."""
    return httpx.AsyncClient(timeout=15.0)
