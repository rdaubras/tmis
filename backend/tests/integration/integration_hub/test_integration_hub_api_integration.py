import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from tmis.main import app


def test_list_connectors_via_api() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/integration-hub/connectors")
    assert response.status_code == 200
    connectors = response.json()
    assert len(connectors) == 7
    ids = {c["id"] for c in connectors}
    assert "crm-demo" in ids
    assert "messaging-demo" in ids


def test_enable_disable_connector_via_api() -> None:
    client = TestClient(app)

    disabled = client.post("/api/v1/integration-hub/connectors/crm-demo/disable")
    assert disabled.status_code == 200
    assert disabled.json()["status"] == "disabled"

    health = client.get("/api/v1/integration-hub/health")
    assert health.status_code == 200
    assert health.json()["status"] == "down"

    enabled = client.post("/api/v1/integration-hub/connectors/crm-demo/enable")
    assert enabled.status_code == 200
    assert enabled.json()["status"] == "active"

    health_again = client.get("/api/v1/integration-hub/health")
    assert health_again.json()["status"] == "up"


def test_disable_unknown_connector_returns_404() -> None:
    client = TestClient(app)
    response = client.post("/api/v1/integration-hub/connectors/unknown/disable")
    assert response.status_code == 404


def test_connector_configuration_roundtrip_via_api() -> None:
    client = TestClient(app)

    set_response = client.put(
        "/api/v1/integration-hub/connectors/calendar-demo/configuration",
        json={"firm_id": "firm-api-1", "values": {"api_key": "abc"}},
    )
    assert set_response.status_code == 200
    assert set_response.json()["values"] == {"api_key": "abc"}

    get_response = client.get(
        "/api/v1/integration-hub/connectors/calendar-demo/configuration",
        params={"firm_id": "firm-api-1"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["values"] == {"api_key": "abc"}


def test_get_configuration_missing_returns_404() -> None:
    client = TestClient(app)
    response = client.get(
        "/api/v1/integration-hub/connectors/calendar-demo/configuration",
        params={"firm_id": "firm-without-config"},
    )
    assert response.status_code == 404


def test_sync_job_create_list_and_run_via_api() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/integration-hub/sync-jobs",
        json={"firm_id": "firm-api-2", "connector_id": "crm-demo", "entity_type": "client"},
    )
    assert created.status_code == 200
    job = created.json()
    assert job["direction"] == "pull"
    assert job["mode"] == "incremental"

    listed = client.get("/api/v1/integration-hub/sync-jobs", params={"firm_id": "firm-api-2"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    run = client.post(
        f"/api/v1/integration-hub/sync-jobs/{job['id']}/run", params={"firm_id": "firm-api-2"}
    )
    assert run.status_code == 200
    result = run.json()
    assert result["job_id"] == job["id"]
    assert result["records_read"] >= 1
    assert result["records_written"] >= 1


def test_run_unknown_sync_job_returns_404() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/integration-hub/sync-jobs/unknown/run", params={"firm_id": "firm-api-2"}
    )
    assert response.status_code == 404


def test_webhook_subscription_and_signed_inbound_delivery_via_api() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/integration-hub/webhooks",
        json={
            "firm_id": "firm-api-3",
            "connector_id": "crm-demo",
            "url": "https://ext.example/hook",
            "direction": "inbound",
            "secret": "shh",
        },
    )
    assert created.status_code == 200
    subscription = created.json()

    body = json.dumps(
        {"entity_type": "client", "external_id": "ext-1", "payload": {"name": "Test"}},
        sort_keys=True,
    ).encode()
    signature = hmac.new(b"shh", body, hashlib.sha256).hexdigest()

    delivered = client.post(
        f"/api/v1/integration-hub/webhooks/{subscription['id']}/inbound",
        json={
            "firm_id": "firm-api-3",
            "entity_type": "client",
            "external_id": "ext-1",
            "payload": {"name": "Test"},
            "signature": signature,
        },
    )
    assert delivered.status_code == 200
    assert delivered.json() is True


def test_webhook_inbound_rejects_bad_signature_via_api() -> None:
    client = TestClient(app)

    created = client.post(
        "/api/v1/integration-hub/webhooks",
        json={
            "firm_id": "firm-api-4",
            "connector_id": "crm-demo",
            "url": "https://ext.example/hook",
            "direction": "inbound",
            "secret": "shh",
        },
    )
    subscription = created.json()

    delivered = client.post(
        f"/api/v1/integration-hub/webhooks/{subscription['id']}/inbound",
        json={
            "firm_id": "firm-api-4",
            "entity_type": "client",
            "external_id": "ext-1",
            "payload": {"name": "Test"},
            "signature": "wrong-signature",
        },
    )
    assert delivered.status_code == 200
    assert delivered.json() is False


def test_webhook_inbound_unknown_subscription_returns_404() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/integration-hub/webhooks/unknown/inbound",
        json={
            "firm_id": "firm-api-5",
            "entity_type": "client",
            "external_id": "ext-1",
            "payload": {},
            "signature": "x",
        },
    )
    assert response.status_code == 404
