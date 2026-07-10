import hashlib

from tmis.platform.feature_flags.ports import FeatureFlagStorePort
from tmis.platform.feature_flags.schemas import FeatureFlag, FlagEvaluationContext


def _bucket(key: str, subject_id: str) -> float:
    """Deterministic, stable [0, 100) bucket for a (flag, subject) pair.

    Uses sha256 rather than the builtin `hash()` because `hash()` is
    randomized per-process (PYTHONHASHSEED) — a subject must land in
    the same bucket every time, on every replica, for a progressive
    rollout to be stable rather than flickering."""

    digest = hashlib.sha256(f"{key}:{subject_id}".encode()).hexdigest()
    return (int(digest[:8], 16) % 10_000) / 100.0


class FeatureFlagEngine:
    """Implements `FeatureFlagEnginePort` (see
    docs/47-guide-securite-entreprise.md — Feature Flags)."""

    def __init__(self, store: FeatureFlagStorePort) -> None:
        self._store = store

    def is_enabled(self, key: str, context: FlagEvaluationContext) -> bool:
        flag = self._store.get(key)
        if flag is None:
            return False
        if not flag.enabled:
            return False
        if context.firm_id is not None and context.firm_id in flag.enabled_firm_ids:
            return True
        if context.user_id is not None and context.user_id in flag.enabled_user_ids:
            return True
        if context.plan is not None and context.plan in flag.enabled_plans:
            return True
        if flag.rollout_percentage <= 0.0:
            return False
        subject_id = context.user_id or context.firm_id
        if subject_id is None:
            return False
        return _bucket(key, subject_id) < flag.rollout_percentage

    def set_flag(self, flag: FeatureFlag) -> FeatureFlag:
        self._store.save(flag)
        return flag
