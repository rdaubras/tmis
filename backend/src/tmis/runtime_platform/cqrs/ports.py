from typing import Any, Protocol


class WriteModelPort(Protocol):
    """A write model folds a domain event into aggregate state — the
    "write side" of CQRS. No existing TMIS domain implements this
    today (the Phase 1 audit found only plain CRUD-style stores);
    this is a foundation for future, progressive adoption, not a
    migration of any domain."""

    def apply(self, event: Any) -> None: ...


class ReadModelPort(Protocol):
    """A read model projects events into a shape optimized for
    querying — the "read side" of CQRS, deliberately decoupled from
    `WriteModelPort` so the two can evolve/scale independently once a
    domain opts in."""

    def project(self, event: Any) -> None: ...

    def get(self, entity_id: str) -> Any | None: ...
