from functools import lru_cache

from tmis.platform.feature_flags.engine import FeatureFlagEngine
from tmis.platform.feature_flags.store import InMemoryFeatureFlagStore


@lru_cache
def get_feature_flag_engine() -> FeatureFlagEngine:
    """Process-wide `FeatureFlagEngine` singleton — see
    docs/47-guide-securite-entreprise.md."""
    return FeatureFlagEngine(InMemoryFeatureFlagStore())
