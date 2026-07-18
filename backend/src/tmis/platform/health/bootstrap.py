from functools import lru_cache

import redis
from sqlalchemy import text

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.core import database as core_database
from tmis.core.config import get_settings
from tmis.platform.health.checks import CallableHealthCheck
from tmis.platform.health.connector_backend_check import ConnectorBackendHealthCheck
from tmis.platform.health.engine import HealthCheckEngine

_REDIS_PROBE_TIMEOUT_SECONDS = 2.0


def _check_database() -> bool:
    """Opens a real connection through the shared SQLAlchemy engine
    (`tmis.core.database.engine`, `pool_pre_ping=True`) and executes
    `SELECT 1` — a stale/unreachable database raises, which
    `CallableHealthCheck.check()` turns into DOWN, never a 500 (see
    docs/49-guide-supervision.md — Health Checks)."""
    with core_database.engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


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
    """Real `PING` against the Redis broker (bounded by a short
    connect/socket timeout so an unreachable Redis can't hang the
    readiness probe) — an exception propagates to
    `CallableHealthCheck.check()`, which reports DOWN with the
    exception message as detail."""
    client = redis.Redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=_REDIS_PROBE_TIMEOUT_SECONDS,
        socket_timeout=_REDIS_PROBE_TIMEOUT_SECONDS,
    )
    try:
        return bool(client.ping())
    finally:
        client.close()


def _check_connectors() -> bool:
    return get_kernel().connector_manager is not None


@lru_cache
def get_health_check_engine() -> HealthCheckEngine:
    """Process-wide `HealthCheckEngine` singleton, pre-registered with
    the seven dependencies the sprint brief names (see
    docs/49-guide-supervision.md), plus `connector_backends` (Sprint 27,
    see docs/154-guide-configuration-connecteurs.md) which reports
    DEGRADED when a connector is running on its in-memory fixture for
    lack of configuration. `database` and `queue` dial the real
    dependency (`SELECT 1`, `PING`); `cache`/`ai_kernel`/`event_bus`/
    `connectors` are structural in-memory checks against the AI
    Kernel, and `storage` always reports healthy since no
    object-storage client exists yet — see each function's docstring.
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
