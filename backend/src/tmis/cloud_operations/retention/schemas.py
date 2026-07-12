from dataclasses import dataclass
from enum import StrEnum


class ObservabilityDataCategory(StrEnum):
    """The four data categories `cloud_operations` itself historizes
    — distinct in scope from `cloud_operations.logging.
    LogRetentionCategory` (log lines specifically) and from
    `platform.compliance.RetentionPolicy` (GDPR personal-data
    retention, keyed by business entity type, not observability
    data)."""

    METRICS = "metrics"
    TRACES = "traces"
    AUDIT_EVENTS = "audit_events"
    INCIDENTS = "incidents"


@dataclass(frozen=True, slots=True)
class ObservabilityRetentionPolicy:
    category: ObservabilityDataCategory
    retention_days: int
