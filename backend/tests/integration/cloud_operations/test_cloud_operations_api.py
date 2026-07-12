import pytest
from fastapi.testclient import TestClient

from tmis.main import app


def test_health_endpoint_reports_all_business_context_checks() -> None:
    client = TestClient(app)
    response = client.get("/cloud-operations/health")
    assert response.status_code == 200
    body = response.json()
    names = {c["name"] for c in body["components"]}
    assert {"ai_fabric", "marketplace", "workflow_engine", "identity_platform"} <= names


def test_alert_rule_can_be_configured_and_evaluated() -> None:
    client = TestClient(app)
    rule = client.post(
        "/cloud-operations/alerts/rules",
        params={
            "name": "high-latency",
            "category": "response_time",
            "comparison": "greater_than",
            "threshold": 500,
        },
    )
    assert rule.status_code == 200
    assert "id" in rule.json()

    evaluated = client.post("/cloud-operations/alerts/evaluate")
    assert evaluated.status_code == 200


def test_dashboards_overview_reflects_platform_and_integrations_state() -> None:
    client = TestClient(app)
    response = client.get("/cloud-operations/dashboards/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["platform_status"] in {"up", "degraded", "down"}
    assert body["integrations_total"] >= 0


def test_incident_can_be_opened_listed_and_resolved() -> None:
    client = TestClient(app)
    opened = client.post(
        "/cloud-operations/incidents",
        params={"title": "Test incident", "description": "desc", "severity": "high"},
    )
    assert opened.status_code == 200
    incident_id = opened.json()["id"]

    listed = client.get("/cloud-operations/incidents")
    assert any(i["id"] == incident_id for i in listed.json())

    resolved = client.post(f"/cloud-operations/incidents/{incident_id}/resolve")
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


def test_runbooks_are_seeded_and_individually_retrievable() -> None:
    client = TestClient(app)
    listed = client.get("/cloud-operations/runbooks")
    assert listed.status_code == 200
    assert len(listed.json()) == 5

    detail = client.get("/cloud-operations/runbooks/ai-provider-unavailable")
    assert detail.status_code == 200
    assert len(detail.json()["steps"]) == 5

    missing = client.get("/cloud-operations/runbooks/does-not-exist")
    assert missing.status_code == 404


def test_diagnostics_endpoint_composes_health_and_performance() -> None:
    client = TestClient(app)
    response = client.get("/cloud-operations/diagnostics")
    assert response.status_code == 200
    body = response.json()
    assert "health_status" in body
    assert "response_time_avg_ms" in body


def test_chaos_scenario_forbidden_in_production_without_authorization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from tmis.cloud_operations import bootstrap as cloud_ops_bootstrap
    from tmis.core.config import Settings

    cloud_ops_bootstrap.get_chaos_testing_engine.cache_clear()
    monkeypatch.setattr(
        cloud_ops_bootstrap,
        "get_settings",
        lambda: Settings(environment="production"),
    )

    client = TestClient(app)
    response = client.post("/cloud-operations/chaos/ai_provider_outage")
    assert response.status_code == 403

    authorized = client.post(
        "/cloud-operations/chaos/ai_provider_outage", params={"authorized": True}
    )
    assert authorized.status_code == 200
    cloud_ops_bootstrap.get_chaos_testing_engine.cache_clear()


def test_request_through_api_is_traced_end_to_end() -> None:
    client = TestClient(app)
    client.get("/")  # any non-cloud-operations route is self-instrumented

    metrics = client.get("/cloud-operations/metrics/response_time")
    assert metrics.status_code == 200
    assert len(metrics.json()["samples"]) >= 1
