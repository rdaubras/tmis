from functools import lru_cache

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.core.config import get_settings
from tmis.platform.health.checks import CallableHealthCheck
from tmis.platform.health.connector_backend_check import ConnectorBackendHealthCheck
from tmis.platform.health.engine import HealthCheckEngine


def _check_database() -> bool:
    """**Known limitation** (see docs/49-guide-supervision.md — Health
    Checks): verifies the connection string is configured, not that
    the database actually answers. Wiring a real `engine.connect()`
    probe needs an async-aware health check port, deferred to when
    TMIS's persistence layer (Sprint "Module Document") lands."""
    return bool(get_settings().database_url)


def _check_cache() -> bool:
    return get_kernel().cache is not None


def _check_storage() -> bool:
    """No dedicated storage client exists yet — `cabinet_os.documents`
    only stores opaque storage-ref strings. Always reports healthy
    until a real object-storage client is wired in."""
    return True


def _check_ai_kernel() -> bool:
    return get_kernel() is not None


def _check_event_bus() -> bool:
    return get_kernel().event_bus is not None


def _check_queue() -> bool:
    """No Celery app is constructed yet in this codebase — reports
    healthy based on configuration presence only."""
    return bool(get_settings().redis_url)


def _check_connectors() -> bool:
    return get_kernel().connector_manager is not None


@lru_cache
def get_health_check_engine() -> HealthCheckEngine:
    """Process-wide `HealthCheckEngine` singleton, pre-registered with
    the seven dependencies the sprint brief names (see
    docs/49-guide-supervision.md), plus `connector_backends` (Sprint 27,
    see docs/154-guide-configuration-connecteurs.md) which reports
    DEGRADED when a connector is running on its in-memory fixture for
    lack of configuration. Every probe here is a lightweight,
    synchronous, structural check — see each function's docstring for
    what it does and does not verify; replacing a probe with a real
    one (an actual `SELECT 1`, a real `PING`) means swapping the
    callable passed to `CallableHealthCheck`, not touching
    `HealthCheckEngine`.
    """
    engine = HealthCheckEngine()
    engine.register(CallableHealthCheck("database", _check_database))
    engine.register(CallableHealthCheck("cache", _check_cache))
    engine.register(CallableHealthCheck("storage", _check_storage))
    engine.register(CallableHealthCheck("ai_kernel", _check_ai_kernel))
    engine.register(CallableHealthCheck("event_bus", _check_event_bus))
    engine.register(CallableHealthCheck("queue", _check_queue))
    engine.register(CallableHealthCheck("connectors", _check_connectors))
    engine.register(ConnectorBackendHealthCheck())
    return engine
