from tmis.business_platform.metering.schemas import MeteredDimension, MeteringEvent


class InMemoryMeteringEventStore:
    def __init__(self) -> None:
        self._events: list[MeteringEvent] = []

    def save(self, event: MeteringEvent) -> None:
        self._events.append(event)

    def list_for_firm(
        self, firm_id: str, dimension: MeteredDimension | None = None
    ) -> list[MeteringEvent]:
        return [
            e
            for e in self._events
            if e.firm_id == firm_id and (dimension is None or e.dimension is dimension)
        ]
