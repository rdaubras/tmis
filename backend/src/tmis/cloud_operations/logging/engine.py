from datetime import UTC, datetime, timedelta

from tmis.cloud_operations.logging.ports import LogRetentionPolicyStorePort
from tmis.cloud_operations.logging.schemas import LogRetentionCategory, LogRetentionPolicy
from tmis.platform.logging.redaction import RedactSensitiveFields

_DEFAULT_RETENTION_DAYS: dict[LogRetentionCategory, int] = {
    LogRetentionCategory.APPLICATION: 30,
    LogRetentionCategory.SECURITY: 365,
    LogRetentionCategory.AUDIT: 2_555,  # 7 years
    LogRetentionCategory.AI_INTERACTION: 90,
}


class LoggingGovernanceEngine:
    """Ties together the four things the sprint's logging strategy
    asks for: severity levels and trace correlation are already
    provided by `core.logging.configure_logging`/`platform.
    observability.correlation_middleware` (Sprint 1/10 — every log
    line already carries `trace_id`, nothing to rebuild here);
    anonymization composes `platform.logging.redaction.
    RedactSensitiveFields` (Sprint 10) directly; retention is the one
    genuinely new piece, a configurable-per-category policy in the
    same spirit as `platform.cache.CachePolicyRegistry`."""

    def __init__(
        self,
        store: LogRetentionPolicyStorePort,
        redactor: RedactSensitiveFields | None = None,
    ) -> None:
        self._store = store
        self._redactor = redactor or RedactSensitiveFields()

    def set_retention(
        self, category: LogRetentionCategory, retention_days: int
    ) -> LogRetentionPolicy:
        policy = LogRetentionPolicy(category=category, retention_days=retention_days)
        self._store.save(policy)
        return policy

    def retention_for(self, category: LogRetentionCategory) -> int:
        policy = self._store.get(category)
        if policy is not None:
            return policy.retention_days
        return _DEFAULT_RETENTION_DAYS[category]

    def redact(self, event_dict: dict[str, object]) -> dict[str, object]:
        return dict(self._redactor(None, "info", event_dict))

    def is_expired(
        self, category: LogRetentionCategory, recorded_at: datetime, *, now: datetime | None = None
    ) -> bool:
        cutoff = (now or datetime.now(UTC)) - timedelta(days=self.retention_for(category))
        return recorded_at < cutoff
