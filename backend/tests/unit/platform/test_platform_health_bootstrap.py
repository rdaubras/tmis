"""Real-dependency behavior of the two probes the deployability sprint
replaced (see docs/49-guide-supervision.md — Health checks): `database`
now runs `SELECT 1` through the shared engine, `queue` now `PING`s Redis.
Both must raise (never swallow) so `CallableHealthCheck.check()` — already
covered by `test_platform_health.py` — is the one place that turns a
failure into `DOWN`."""

import pytest
from sqlalchemy import create_engine

from tmis.core import database as core_database
from tmis.core.config import Settings
from tmis.platform.health import bootstrap

_UNREACHABLE_REDIS_URL = "redis://127.0.0.1:1/0"
_UNREACHABLE_DATABASE_URL = "postgresql+psycopg://tmis:tmis@127.0.0.1:1/tmis"


def test_check_database_is_up_against_the_real_engine() -> None:
    assert bootstrap._check_database() is True  # noqa: SLF001


def test_check_database_raises_when_the_database_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(core_database, "engine", create_engine(_UNREACHABLE_DATABASE_URL))

    with pytest.raises(Exception):  # noqa: B017, PT011 — any DB-ish exception counts as DOWN
        bootstrap._check_database()  # noqa: SLF001


def test_check_queue_is_up_when_redis_answers_a_ping(
    monkeypatch: pytest.MonkeyPatch, redis_ping_server: str
) -> None:
    monkeypatch.setattr(
        bootstrap, "get_settings", lambda: Settings(debug=True, redis_url=redis_ping_server)
    )

    assert bootstrap._check_queue() is True  # noqa: SLF001


def test_check_queue_raises_when_redis_is_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "get_settings",
        lambda: Settings(debug=True, redis_url=_UNREACHABLE_REDIS_URL),
    )

    with pytest.raises(Exception):  # noqa: B017, PT011 — any redis-ish exception counts as DOWN
        bootstrap._check_queue()  # noqa: SLF001
