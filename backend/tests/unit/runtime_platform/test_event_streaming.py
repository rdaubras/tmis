import asyncio

from tmis.runtime_platform.event_streaming.engine import EventStreamingEngine


class _FakeEvent:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeBus:
    def __init__(self) -> None:
        self._history: list[object] = []

    async def publish(self, event: object) -> None:
        self._history.append(event)

    @property
    def history(self) -> list[object]:
        return list(self._history)


def test_publish_forwards_to_wrapped_bus_and_records_envelope() -> None:
    async def scenario() -> None:
        bus = _FakeBus()
        streaming = EventStreamingEngine(bus, schema_version=2)

        envelope = await streaming.publish(_FakeEvent("a"))

        assert envelope is not None
        assert envelope.sequence == 1
        assert envelope.version == 2
        assert envelope.event_type == "_FakeEvent"
        assert len(bus.history) == 1

    asyncio.run(scenario())


def test_idempotency_key_dedups_publish() -> None:
    async def scenario() -> None:
        bus = _FakeBus()
        streaming = EventStreamingEngine(bus)

        first = await streaming.publish(_FakeEvent("a"), idempotency_key="k1")
        second = await streaming.publish(_FakeEvent("a-dup"), idempotency_key="k1")

        assert first is not None
        assert second is None
        assert len(bus.history) == 1

    asyncio.run(scenario())


def test_replay_returns_ordered_active_envelopes() -> None:
    async def scenario() -> None:
        bus = _FakeBus()
        streaming = EventStreamingEngine(bus)
        for i in range(3):
            await streaming.publish(_FakeEvent(str(i)))

        replayed = streaming.replay(from_sequence=1)
        assert [e.sequence for e in replayed] == [2, 3]

    asyncio.run(scenario())


def test_archive_excludes_from_replay_but_keeps_in_archived() -> None:
    async def scenario() -> None:
        bus = _FakeBus()
        streaming = EventStreamingEngine(bus)
        for i in range(3):
            await streaming.publish(_FakeEvent(str(i)))

        archived_count = streaming.archive(before_sequence=2)
        assert archived_count == 1
        assert [e.sequence for e in streaming.replay()] == [2, 3]
        assert [e.sequence for e in streaming.archived()] == [1]

    asyncio.run(scenario())
