from typing import Any, Protocol


class PublishableEventBusPort(Protocol):
    """The minimal shape every existing TMIS event bus already
    shares (`async publish(event)` + a `.history` list) — narrow
    enough that `EventStreamingEngine` can decorate any of the seven
    without depending on any single bus's concrete event hierarchy."""

    async def publish(self, event: Any) -> None: ...

    @property
    def history(self) -> list[Any]: ...
