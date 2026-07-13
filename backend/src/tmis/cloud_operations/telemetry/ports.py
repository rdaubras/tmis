from typing import Protocol

from tmis.cloud_operations.telemetry.schemas import TelemetryEvent


class TelemetryEventStorePort(Protocol):
    def save(self, event: TelemetryEvent) -> None: ...

    def list_for_firm(self, firm_id: str) -> list[TelemetryEvent]: ...

    def list_all(self) -> list[TelemetryEvent]: ...
