from datetime import UTC, datetime, timedelta

from tmis.cloud_operations.retention.ports import ObservabilityRetentionPolicyStorePort
from tmis.cloud_operations.retention.schemas import (
    ObservabilityDataCategory,
    ObservabilityRetentionPolicy,
)

_DEFAULT_RETENTION_DAYS: dict[ObservabilityDataCategory, int] = {
    ObservabilityDataCategory.METRICS: 90,
    ObservabilityDataCategory.TRACES: 30,
    ObservabilityDataCategory.AUDIT_EVENTS: 2_555,  # 7 years, matches logging.AUDIT
    ObservabilityDataCategory.INCIDENTS: 365,
}


class RetentionEngine:
    """Retention policy for `cloud_operations`' own historized data
    (metrics/traces/audit events/incidents) — mirrors
    `cloud_operations.logging.LoggingGovernanceEngine`'s
    category→retention_days pattern (Sprint 21), scoped to
    observability data rather than log lines."""

    def __init__(self, store: ObservabilityRetentionPolicyStorePort) -> None:
        self._store = store

    def set_retention(
        self, category: ObservabilityDataCategory, retention_days: int
    ) -> ObservabilityRetentionPolicy:
        policy = ObservabilityRetentionPolicy(category=category, retention_days=retention_days)
        self._store.save(policy)
        return policy

    def retention_for(self, category: ObservabilityDataCategory) -> int:
        policy = self._store.get(category)
        if policy is not None:
            return policy.retention_days
        return _DEFAULT_RETENTION_DAYS[category]

    def is_expired(
        self,
        category: ObservabilityDataCategory,
        recorded_at: datetime,
        *,
        now: datetime | None = None,
    ) -> bool:
        cutoff = (now or datetime.now(UTC)) - timedelta(days=self.retention_for(category))
        return recorded_at < cutoff
