"""The tests that would have caught the "green in CI, broken at deploy"
episode this sprint closes (see the sprint brief, plan de tests §1-4):
`/platform/health/ready` must actually go DOWN when the database or Redis
is unreachable, and the liveness/`/api/v1/health` probes must stay
dependency-free regardless."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from tmis.core import database as core_database
from tmis.core.config import Settings
from tmis.main import app
from tmis.platform.health import bootstrap

_UNREACHABLE_REDIS_URL = "redis://127.0.0.1:1/0"
_UNREACHABLE_DATABASE_URL = "postgresql+psycopg://tmis:tmis@127.0.0.1:1/tmis"


def test_readiness_returns_503_when_the_database_is_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(core_database, "engine", create_engine(_UNREACHABLE_DATABASE_URL))

    response = TestClient(app).get("/platform/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "down"
    database_component = next(c for c in body["components"] if c["name"] == "database")
    assert database_component["status"] == "down"


def test_readiness_returns_503_when_redis_is_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bootstrap,
        "get_settings",
        lambda: Settings(debug=True, redis_url=_UNREACHABLE_REDIS_URL),
    )

    response = TestClient(app).get("/platform/health/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "down"
    queue_component = next(c for c in body["components"] if c["name"] == "queue")
    assert queue_component["status"] == "down"


def test_readiness_reports_database_and_queue_up_when_both_answer(
    monkeypatch: pytest.MonkeyPatch, redis_ping_server: str
) -> None:
    monkeypatch.setattr(
        bootstrap, "get_settings", lambda: Settings(debug=True, redis_url=redis_ping_server)
    )

    response = TestClient(app).get("/platform/health/ready")

    assert response.status_code == 200
    body = response.json()
    database_component = next(c for c in body["components"] if c["name"] == "database")
    queue_component = next(c for c in body["components"] if c["name"] == "queue")
    assert database_component["status"] == "up"
    assert queue_component["status"] == "up"


def test_liveness_stays_up_when_the_database_and_redis_are_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(core_database, "engine", create_engine(_UNREACHABLE_DATABASE_URL))
    monkeypatch.setattr(
        bootstrap,
        "get_settings",
        lambda: Settings(debug=True, redis_url=_UNREACHABLE_REDIS_URL),
    )

    response = TestClient(app).get("/platform/health/live")

    assert response.status_code == 200
    assert response.text == "up"


def test_api_v1_health_stays_ok_when_the_database_and_redis_are_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(core_database, "engine", create_engine(_UNREACHABLE_DATABASE_URL))
    monkeypatch.setattr(
        bootstrap,
        "get_settings",
        lambda: Settings(debug=True, redis_url=_UNREACHABLE_REDIS_URL),
    )

    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
