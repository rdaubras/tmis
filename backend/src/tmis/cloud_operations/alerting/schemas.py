import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from tmis.cloud_operations.metrics.schemas import MetricCategory


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertComparison(StrEnum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"


def new_alert_rule_id() -> str:
    return f"alr-{uuid.uuid4().hex[:12]}"


def new_alert_event_id() -> str:
    return f"ale-{uuid.uuid4().hex[:12]}"


@dataclass(slots=True)
class AlertRule:
    """A configurable threshold on one `metrics.MetricCategory` — the
    sprint's examples ("augmentation du temps de réponse, taux
    d'erreur élevé, échec d'un workflow critique, indisponibilité
    d'un fournisseur IA, dépassement des quotas") are all expressible
    as a threshold on a metric category, so this rule shape covers
    all five rather than needing five bespoke alert types."""

    id: str
    name: str
    category: MetricCategory
    comparison: AlertComparison
    threshold: float
    severity: AlertSeverity = AlertSeverity.WARNING
    firm_id: str | None = None
    notify_recipient_id: str | None = None
    active: bool = True


@dataclass(frozen=True, slots=True)
class AlertEvent:
    id: str
    rule_id: str
    rule_name: str
    severity: AlertSeverity
    observed_value: float
    threshold: float
    firm_id: str | None
    triggered_at: datetime = field(default_factory=lambda: datetime.now(UTC))
