import json
from abc import ABC, abstractmethod
from typing import Any

from tmis.ai.cache.factory import make_cache
from tmis.ai.cache.ports import CachePort
from tmis.platform_sdk.connector_sdk.schemas import ConnectorPage, ConnectorResult
from tmis.platform_sdk.plugin_system.schemas import PluginType
from tmis.platform_sdk.sdk.schemas import PluginContext

_DEFAULT_CACHE_TTL_SECONDS = 300


class BaseConnectorPlugin(ABC):
    """The sprint's "CONNECTOR SDK": authentification, pagination,
    gestion des erreurs, normalisation des résultats, cache — built
    once here so every connector plugin gets the same behavior for
    free and only implements `fetch_page()` (one page of raw results)
    and, optionally, `normalize()`. Caching reuses
    `tmis.ai.cache.ports.CachePort` (Sprint 2) rather than a new cache
    abstraction — `InMemoryCache` by default, `RedisCache` in production
    when Redis is reachable (Sprint 28, see `tmis.ai.cache.factory.
    make_cache`), same as the AI Kernel."""

    plugin_type = PluginType.CONNECTOR

    def __init__(self, plugin_id: str, cache: CachePort | None = None) -> None:
        self.id = plugin_id
        self._cache: CachePort = cache if cache is not None else make_cache()

    async def authenticate(self, context: PluginContext) -> None:  # noqa: B027
        """Override to perform a real handshake; a no-op by default
        (many connectors are unauthenticated or use a static key
        already resolved into `context.config`)."""

    @abstractmethod
    async def fetch_page(self, query: str, page: int) -> ConnectorPage: ...

    def normalize(self, item: dict[str, Any]) -> dict[str, Any]:
        """Identity by default — override to reshape source-specific
        fields into TMIS's common result shape."""
        return item

    async def search(
        self, context: PluginContext, query: str, max_pages: int = 1
    ) -> ConnectorResult:
        cache_key = f"connector:{self.id}:{query}:{max_pages}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return ConnectorResult(items=tuple(json.loads(cached)))

        await self.authenticate(context)
        items: list[dict[str, Any]] = []
        warnings: list[str] = []
        page = 1
        while page <= max_pages:
            try:
                result_page = await self.fetch_page(query, page)
            except Exception as exc:  # noqa: BLE001 — a connector error must never crash the caller
                warnings.append(f"page {page} failed: {exc}")
                break
            items.extend(self.normalize(item) for item in result_page.items)
            if not result_page.has_next:
                break
            page += 1

        await self._cache.set(
            cache_key, json.dumps(items), ttl_seconds=_DEFAULT_CACHE_TTL_SECONDS
        )
        return ConnectorResult(items=tuple(items), warnings=tuple(warnings))

    async def invoke(self, context: PluginContext, payload: dict[str, Any]) -> dict[str, Any]:
        result = await self.search(
            context, str(payload.get("query", "")), int(payload.get("max_pages", 1))
        )
        return {"items": list(result.items), "warnings": list(result.warnings)}
