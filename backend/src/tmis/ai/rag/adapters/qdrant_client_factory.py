from functools import lru_cache

from qdrant_client import AsyncQdrantClient

from tmis.core.config import get_settings


@lru_cache
def get_qdrant_client() -> AsyncQdrantClient:
    """Process-wide `AsyncQdrantClient` singleton, built once from the
    central config (see `tmis.core.config.Settings`) — every caller that
    needs Qdrant (today: `QdrantVectorIndex`) shares this client instead of
    opening its own connection."""
    settings = get_settings()
    return AsyncQdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        timeout=int(settings.qdrant_timeout_seconds),
        # A compatibility check dials the server eagerly at construction
        # time; deferred to the first real call instead, so building the
        # client never depends on Qdrant already being reachable (mirrors
        # every other adapter here: nothing pings its backend at
        # construction, only when actually used).
        check_compatibility=False,
    )
