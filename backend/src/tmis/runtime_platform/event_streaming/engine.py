from typing import Any

from tmis.runtime_platform.event_streaming.ports import PublishableEventBusPort
from tmis.runtime_platform.event_streaming.schemas import EventEnvelope


class EventStreamingEngine:
    """Decorates any existing TMIS event bus (see `ports.
    PublishableEventBusPort`) with replay, ordering, idempotency,
    versioning and archival — without replacing the bus's own
    subscriber dispatch. A caller publishes through this engine
    instead of calling `bus.publish` directly; the engine forwards to
    the wrapped bus and additionally records an `EventEnvelope`."""

    def __init__(self, bus: PublishableEventBusPort, *, schema_version: int = 1) -> None:
        self._bus = bus
        self._schema_version = schema_version
        self._envelopes: list[EventEnvelope] = []
        self._seen_idempotency_keys: set[str] = set()
        self._next_sequence = 1

    async def publish(
        self, event: Any, *, idempotency_key: str | None = None
    ) -> EventEnvelope | None:
        """Returns `None` without publishing if `idempotency_key` was
        already seen — the dedup guarantee no wrapped bus provides on
        its own."""
        if idempotency_key is not None and idempotency_key in self._seen_idempotency_keys:
            return None
        await self._bus.publish(event)
        envelope = EventEnvelope(
            sequence=self._next_sequence,
            event=event,
            event_type=type(event).__name__,
            version=self._schema_version,
            idempotency_key=idempotency_key,
        )
        self._next_sequence += 1
        self._envelopes.append(envelope)
        if idempotency_key is not None:
            self._seen_idempotency_keys.add(idempotency_key)
        return envelope

    def replay(self, from_sequence: int = 0) -> list[EventEnvelope]:
        """Active (non-archived) envelopes after `from_sequence`, in
        publish order — the ordering guarantee."""
        return [e for e in self._envelopes if e.sequence > from_sequence and not e.archived]

    def archive(self, before_sequence: int) -> int:
        count = 0
        for envelope in self._envelopes:
            if envelope.sequence < before_sequence and not envelope.archived:
                envelope.archived = True
                count += 1
        return count

    def archived(self) -> list[EventEnvelope]:
        return [e for e in self._envelopes if e.archived]

    @property
    def history(self) -> list[EventEnvelope]:
        return list(self._envelopes)
