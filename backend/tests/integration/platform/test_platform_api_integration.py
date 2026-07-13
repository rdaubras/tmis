from fastapi.testclient import TestClient

from tmis.main import app


def test_platform_health_live_is_always_up() -> None:
    client = TestClient(app)

    response = client.get("/platform/health/live")

    assert response.status_code == 200
    assert response.text == "up"


def test_platform_health_ready_reports_component_statuses() -> None:
    client = TestClient(app)

    response = client.get("/platform/health/ready")

    assert response.status_code in (200, 503)
    body = response.json()
    assert "status" in body
    assert isinstance(body["components"], list)
    # 7 platform checks (Sprint 10) plus, once `cloud_operations`
    # (Sprint 21) has registered its five business-context checks into
    # this same shared engine, 12 — the exact count depends on whether
    # a `cloud_operations` endpoint has already run in this process, so
    # this asserts the floor rather than an exact, ever-growing number.
    assert len(body["components"]) >= 7


def test_platform_metrics_exposes_prometheus_text_format() -> None:
    client = TestClient(app)

    client.get("/platform/health/live")
    response = client.get("/platform/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text


def test_platform_monitoring_dashboard_returns_a_snapshot() -> None:
    client = TestClient(app)

    response = client.get("/platform/monitoring")

    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "total_requests" in body
    assert "ai_cost_usd_total" in body


def test_every_response_carries_the_hardened_security_headers() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_csrf_middleware_is_a_noop_for_bearer_token_style_requests() -> None:
    """TMIS authenticates with a JWT bearer token, never a cookie, so a
    POST without any CSRF cookie must not be blocked (see
    docs/47-guide-securite-entreprise.md — CSRF)."""
    client = TestClient(app)

    response = client.post("/platform/health/live")

    assert response.status_code != 403


def test_csrf_middleware_blocks_a_mismatched_double_submit_cookie() -> None:
    client = TestClient(app)
    client.cookies.set("csrf_token", "cookie-value")

    response = client.post(
        "/platform/health/live", headers={"X-CSRF-Token": "different-header-value"}
    )

    assert response.status_code == 403


def test_csrf_middleware_allows_a_matching_double_submit_cookie() -> None:
    client = TestClient(app)
    client.cookies.set("csrf_token", "matching-value")

    response = client.post("/platform/health/live", headers={"X-CSRF-Token": "matching-value"})

    assert response.status_code != 403
