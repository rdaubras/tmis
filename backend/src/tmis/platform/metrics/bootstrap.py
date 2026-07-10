from functools import lru_cache

from tmis.platform.metrics.registry import MetricsRegistry


@lru_cache
def get_metrics_registry() -> MetricsRegistry:
    """Process-wide `MetricsRegistry` singleton — every metric TMIS
    records (HTTP requests, AI cost, cache hits...) shares this one
    registry so a single `/metrics` endpoint can render all of them
    (see docs/49-guide-supervision.md)."""
    return MetricsRegistry()
