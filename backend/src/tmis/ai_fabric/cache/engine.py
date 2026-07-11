from tmis.ai.cache.ports import CachePort
from tmis.ai_fabric.cache.schemas import build_cache_key


class ResponseCache:
    """The sprint's "CACHE" module: avoids re-invoking a model for a
    (task type, model, prompt) combination already answered. Reuses
    `tmis.ai.cache.CachePort` (Sprint 2) as its backend rather than
    inventing a new caching abstraction — `tmis.ai_fabric.cost_optimizer`
    consults this cache before considering a paid model call, and
    `tmis.ai_fabric.token_manager` records the resulting cache-hit rate."""

    def __init__(self, backend: CachePort, *, default_ttl_seconds: int | None = 3600) -> None:
        self._backend = backend
        self._default_ttl_seconds = default_ttl_seconds

    async def get(self, task_type: str, model_name: str, prompt: str) -> str | None:
        key = build_cache_key(task_type, model_name, prompt)
        return await self._backend.get(key)

    async def set(
        self,
        task_type: str,
        model_name: str,
        prompt: str,
        response_text: str,
        *,
        ttl_seconds: int | None = None,
    ) -> None:
        key = build_cache_key(task_type, model_name, prompt)
        await self._backend.set(
            key, response_text, ttl_seconds=ttl_seconds or self._default_ttl_seconds
        )

    async def invalidate(self, task_type: str, model_name: str, prompt: str) -> None:
        key = build_cache_key(task_type, model_name, prompt)
        await self._backend.delete(key)
