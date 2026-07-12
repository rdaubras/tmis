from tmis.cloud_operations.telemetry.schemas import TelemetryEvent


class InMemoryTelemetryEventStore:
    def __init__(self) -> None:
        self._events: list[TelemetryEvent] = []

    def save(self, event: TelemetryEvent) -> None:
        self._events.append(event)

    def list_for_firm(self, firm_id: str) -> list[TelemetryEvent]:
        return [e for e in self._events if e.firm_id == firm_id]

    def list_all(self) -> list[TelemetryEvent]:
        return list(self._events)
