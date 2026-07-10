import time
from collections.abc import Callable

from tmis.platform.health.schemas import ComponentHealth, HealthStatus


class CallableHealthCheck:
    """Implements `HealthCheckPort` by wrapping a plain probe callable
    — one adapter for all seven dependencies the sprint brief names
    (database, cache, storage, AI Kernel, event bus, queue,
    connectors), rather than seven bespoke classes each hardcoding a
    specific client library (see docs/49-guide-supervision.md — Health
    Checks). A deployment wires a real probe (`engine.connect()`,
    `redis.ping()`...) per dependency at bootstrap time.

    `probe` returning `True` means UP; returning `False` means DOWN;
    raising an exception is also treated as DOWN, with the exception
    message as the detail — a broken probe never crashes the health
    endpoint."""

    def __init__(self, name: str, probe: Callable[[], bool]) -> None:
        self._name = name
        self._probe = probe

    def check(self) -> ComponentHealth:
        start = time.perf_counter()
        try:
            healthy = self._probe()
        except Exception as exc:  # noqa: BLE001 — a failing probe must never crash health checks
            latency_ms = (time.perf_counter() - start) * 1000
            return ComponentHealth(
                name=self._name, status=HealthStatus.DOWN, detail=str(exc), latency_ms=latency_ms
            )
        latency_ms = (time.perf_counter() - start) * 1000
        status = HealthStatus.UP if healthy else HealthStatus.DOWN
        return ComponentHealth(name=self._name, status=status, latency_ms=latency_ms)
