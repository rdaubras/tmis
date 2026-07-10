from typing import Protocol

from tmis.platform.health.schemas import ComponentHealth, SystemHealth


class HealthCheckPort(Protocol):
    """Port implemented by every interchangeable dependency check —
    database, cache, storage, AI Kernel, event bus, queue, connectors
    (see docs/49-guide-supervision.md — Health Checks)."""

    def check(self) -> ComponentHealth: ...


class HealthCheckEnginePort(Protocol):
    """Port implemented by every interchangeable health-check engine."""

    def register(self, check: HealthCheckPort) -> None: ...

    def liveness(self) -> SystemHealth: ...

    def readiness(self) -> SystemHealth: ...
