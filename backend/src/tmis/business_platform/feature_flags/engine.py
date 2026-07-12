import hashlib
from datetime import UTC, datetime

from tmis.business_platform.feature_flags.ports import BusinessFlagExtrasStorePort
from tmis.business_platform.feature_flags.schemas import BusinessFlagContext, BusinessFlagExtras
from tmis.platform.feature_flags.engine import FeatureFlagEngine
from tmis.platform.feature_flags.schemas import FlagEvaluationContext


def _bucket(experiment_key: str, subject_id: str) -> float:
    digest = hashlib.sha256(f"{experiment_key}:{subject_id}".encode()).hexdigest()
    return (int(digest[:8], 16) % 10_000) / 100.0


class BusinessFeatureFlagEngine:
    """Wraps `platform.feature_flags.FeatureFlagEngine` (Sprint 10,
    kill switch + firm/user allow-list + plan allow-list + percentage
    rollout) rather than reimplementing it, and layers the four extra
    gating dimensions the sprint asks for — environment, group, time
    window, experiment — on top via `BusinessFlagExtras`. A key must
    still pass the base engine's evaluation *and* every extras
    dimension present for that key."""

    def __init__(self, base: FeatureFlagEngine, extras_store: BusinessFlagExtrasStorePort) -> None:
        self._base = base
        self._extras_store = extras_store

    def is_enabled(self, key: str, context: BusinessFlagContext) -> bool:
        base_context = FlagEvaluationContext(firm_id=context.firm_id, user_id=context.user_id)
        if not self._base.is_enabled(key, base_context):
            return False

        extras = self._extras_store.get(key)
        if extras is None:
            return True

        if extras.enabled_environments and context.environment not in extras.enabled_environments:
            return False
        if extras.enabled_group_ids and not (context.group_ids & extras.enabled_group_ids):
            return False
        if extras.enabled_plans and context.plan_name not in extras.enabled_plans:
            return False

        now = context.now or datetime.now(UTC)
        if extras.window_start is not None and now < extras.window_start:
            return False
        if extras.window_end is not None and now > extras.window_end:
            return False

        if extras.experiment_key is not None:
            subject_id = context.user_id or context.firm_id
            if subject_id is None:
                return False
            if _bucket(extras.experiment_key, subject_id) >= extras.experiment_rollout_percentage:
                return False

        return True

    def set_extras(self, extras: BusinessFlagExtras) -> BusinessFlagExtras:
        self._extras_store.save(extras)
        return extras
