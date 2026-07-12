from fastapi.testclient import TestClient

from tmis.main import app


def test_audit_timeline_endpoint_returns_empty_list_for_unknown_firm() -> None:
    client = TestClient(app)
    response = client.get("/cloud-operations/audit/firm-unknown")
    assert response.status_code == 200
    assert response.json() == []


def test_cost_snapshot_endpoint_returns_zeroed_snapshot_for_new_firm() -> None:
    client = TestClient(app)
    response = client.get("/cloud-operations/cost/firm-cost-1")
    assert response.status_code == 200
    body = response.json()
    assert body["firm_id"] == "firm-cost-1"
    assert body["total_cost_usd"] == 0


def test_ai_quality_scan_endpoint_detects_unsupported_claims() -> None:
    client = TestClient(app)
    response = client.post(
        "/cloud-operations/ai-quality/firm-1/scan",
        params={"text": "Une affirmation grave sans aucune source ni référence."},
    )
    assert response.status_code == 200
    incidents = response.json()
    assert any(i["kind"] == "hallucination" for i in incidents)

    recent = client.get("/cloud-operations/ai-quality/incidents/recent")
    assert recent.status_code == 200
    assert len(recent.json()) >= 1


def test_workflow_monitoring_endpoint_returns_a_snapshot() -> None:
    client = TestClient(app)
    response = client.get("/cloud-operations/workflow-monitoring")
    assert response.status_code == 200
    body = response.json()
    assert "total_runs" in body
    assert "average_duration_ms" in body


def test_integration_monitoring_endpoint_returns_a_list() -> None:
    client = TestClient(app)
    response = client.get("/cloud-operations/integration-monitoring")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tenant_monitoring_endpoint_returns_404_for_firm_without_subscription() -> None:
    client = TestClient(app)
    response = client.get("/cloud-operations/tenants/firm-unknown-tenant")
    assert response.status_code == 404


def test_security_monitoring_endpoint_returns_a_snapshot() -> None:
    client = TestClient(app)
    response = client.get("/cloud-operations/security-monitoring")
    assert response.status_code == 200
    body = response.json()
    assert "total_events" in body
    assert "events_by_type" in body


def test_retention_can_be_read_and_updated() -> None:
    client = TestClient(app)
    read = client.get("/cloud-operations/retention/traces")
    assert read.status_code == 200
    assert read.json()["retention_days"] == 30

    written = client.post("/cloud-operations/retention/traces", params={"retention_days": 5})
    assert written.status_code == 200
    assert written.json()["retention_days"] == 5

    reread = client.get("/cloud-operations/retention/traces")
    assert reread.json()["retention_days"] == 5


def test_export_incidents_as_json() -> None:
    client = TestClient(app)
    opened = client.post(
        "/cloud-operations/incidents",
        params={
            "title": "Export test",
            "description": "d",
            "severity": "low",
            "firm_id": "firm-export",
        },
    )
    assert opened.status_code == 200

    exported = client.get(
        "/cloud-operations/exports/incidents",
        params={"export_format": "json", "firm_id": "firm-export"},
    )
    assert exported.status_code == 200
    assert exported.json()["filename"] == "incidents.json"
    assert "Export test" in exported.json()["content"]


def test_export_metrics_as_csv() -> None:
    client = TestClient(app)
    client.get("/")  # generates at least one RESPONSE_TIME metric sample

    exported = client.get(
        "/cloud-operations/exports/metrics/response_time", params={"export_format": "csv"}
    )
    assert exported.status_code == 200
    assert exported.json()["filename"] == "metrics.csv"
