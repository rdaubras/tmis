from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IntegrationMonitoringSnapshot:
    connector_id: str
    total_operations: int
    success_rate: float
    average_duration_ms: float
