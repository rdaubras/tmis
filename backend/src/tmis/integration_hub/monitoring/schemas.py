from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class ConnectorOperationMetric:
    connector_id: str
    firm_id: str
    operation: str
    success: bool
    duration_ms: float
    record_count: int = 0
    error: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(UTC))
