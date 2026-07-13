import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class SLAMetricType(StrEnum):
    """The four indicators the sprint asks the SLA engine to measure
    ("disponibilité, latence, taux de réussite, temps de
    restauration"). Availability/success_rate are "higher is better"
    (percentages); latency/restoration_time are "lower is better"
    (milliseconds/minutes) — `SLAEngine._is_met` branches on this."""

    AVAILABILITY = "availability"
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    RESTORATION_TIME = "restoration_time"


_LOWER_IS_BETTER = frozenset({SLAMetricType.LATENCY, SLAMetricType.RESTORATION_TIME})


def new_sla_target_id() -> str:
    return f"slat-{uuid.uuid4().hex[:12]}"


def new_sla_sample_id() -> str:
    return f"slas-{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True, slots=True)
class SLATarget:
    id: str
    service_name: str
    metric_type: SLAMetricType
    target_value: float


@dataclass(frozen=True, slots=True)
class SLASample:
    id: str
    service_name: str
    metric_type: SLAMetricType
    value: float
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(frozen=True, slots=True)
class SLAIndicator:
    service_name: str
    metric_type: SLAMetricType
    target_value: float
    actual_value: float
    met: bool
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
