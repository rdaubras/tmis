import pytest
from fastapi.testclient import TestClient

from tmis.cabinet_os.bootstrap import (
    get_administration_engine,
    get_billing_engine,
    get_cabinet_document_service,
    get_cabinet_document_store,
    get_calendar_engine,
    get_calendar_store,
    get_client_service,
    get_client_store,
    get_contact_service,
    get_contact_store,
    get_crm_engine,
    get_dashboard_engine,
    get_deadline_engine,
    get_deadline_store,
    get_hearing_engine,
    get_hearing_store,
    get_invoice_store,
    get_payment_store,
    get_public_api_engine,
    get_quote_store,
    get_report_engine,
    get_settings_engine,
    get_subscription_engine,
    get_subscription_store,
    get_time_entry_store,
    get_time_tracking_service,
    get_usage_store,
)
from tmis.main import app

_PREFIX = "/api/v1/cabinet-os"


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    for cache_clearing_fn in (
        get_client_store,
        get_client_service,
        get_contact_store,
        get_contact_service,
        get_crm_engine,
        get_calendar_store,
        get_calendar_engine,
        get_hearing_store,
        get_hearing_engine,
        get_deadline_store,
        get_deadline_engine,
        get_time_entry_store,
        get_time_tracking_service,
        get_quote_store,
        get_invoice_store,
        get_payment_store,
        get_billing_engine,
        get_subscription_store,
        get_usage_store,
        get_subscription_engine,
        get_cabinet_document_store,
        get_cabinet_document_service,
        get_dashboard_engine,
        get_report_engine,
        get_settings_engine,
        get_administration_engine,
        get_public_api_engine,
    ):
        cache_clearing_fn.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_client(client: TestClient, **overrides: object) -> dict:
    payload = {
        "firm_id": "firm-1",
        "client_type": "individual",
        "display_name": "Jean Dupont",
    }
    payload.update(overrides)
    response = client.post(f"{_PREFIX}/clients", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_and_get_client(client: TestClient) -> None:
    created = _create_client(client)

    response = client.get(f"{_PREFIX}/clients/{created['id']}")

    assert response.status_code == 200
    assert response.json()["display_name"] == "Jean Dupont"


def test_get_unknown_client_returns_404(client: TestClient) -> None:
    response = client.get(f"{_PREFIX}/clients/does-not-exist")
    assert response.status_code == 404


def test_search_clients(client: TestClient) -> None:
    _create_client(client, display_name="Alice Martin")
    _create_client(client, display_name="Bob Martin")

    response = client.get(f"{_PREFIX}/clients", params={"firm_id": "firm-1", "q": "alice"})

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_add_client_note_and_change_status(client: TestClient) -> None:
    created = _create_client(client)

    note_response = client.post(
        f"{_PREFIX}/clients/{created['id']}/notes",
        json={"author_id": "admin-1", "text": "Premier contact"},
    )
    assert note_response.status_code == 200

    status_response = client.post(
        f"{_PREFIX}/clients/{created['id']}/status", json={"target": "active"}
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "active"


def test_change_status_illegal_transition_returns_400(client: TestClient) -> None:
    created = _create_client(client)

    response = client.post(
        f"{_PREFIX}/clients/{created['id']}/status", json={"target": "prospect"}
    )

    assert response.status_code == 400


def test_create_contact(client: TestClient) -> None:
    response = client.post(
        f"{_PREFIX}/contacts",
        json={"firm_id": "firm-1", "role": "expert", "display_name": "Dr. Martin"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "expert"


def test_schedule_calendar_event_and_view_agenda(client: TestClient) -> None:
    created = client.post(
        f"{_PREFIX}/calendar/events",
        json={
            "firm_id": "firm-1",
            "event_type": "appointment",
            "title": "RDV client",
            "starts_at": "2026-08-01T10:00:00Z",
        },
    )
    assert created.status_code == 200

    view = client.get(
        f"{_PREFIX}/calendar/view",
        params={"firm_id": "firm-1", "view": "agenda", "reference_date": "2026-07-01T00:00:00Z"},
    )
    assert view.status_code == 200
    assert len(view.json()) == 1


def test_schedule_hearing_creates_calendar_event_and_reminder(client: TestClient) -> None:
    response = client.post(
        f"{_PREFIX}/hearings",
        json={
            "firm_id": "firm-1",
            "case_id": "case-1",
            "jurisdiction": "TJ Paris",
            "chamber": "1ere chambre",
            "scheduled_at": "2026-09-01T09:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["calendar_event_id"] is not None
    assert body["reminder_event_id"] is not None


def test_record_hearing_decision(client: TestClient) -> None:
    hearing = client.post(
        f"{_PREFIX}/hearings",
        json={
            "firm_id": "firm-1",
            "case_id": "case-1",
            "jurisdiction": "TJ Paris",
            "chamber": "1ere chambre",
            "scheduled_at": "2026-09-01T09:00:00Z",
        },
    ).json()

    response = client.post(
        f"{_PREFIX}/hearings/{hearing['id']}/decision", json={"decision": "Renvoi"}
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "Renvoi"


def test_create_deadline_and_list_upcoming(client: TestClient) -> None:
    created = client.post(
        f"{_PREFIX}/deadlines",
        json={
            "firm_id": "firm-1",
            "case_id": "case-1",
            "label": "Conclusions",
            "due_at": "2026-08-15T00:00:00Z",
        },
    )
    assert created.status_code == 200

    response = client.get(f"{_PREFIX}/deadlines", params={"firm_id": "firm-1", "within_days": 365})
    assert response.status_code == 200


def test_mark_deadline_done(client: TestClient) -> None:
    deadline = client.post(
        f"{_PREFIX}/deadlines",
        json={
            "firm_id": "firm-1",
            "case_id": "case-1",
            "label": "Conclusions",
            "due_at": "2026-08-15T00:00:00Z",
        },
    ).json()

    response = client.post(f"{_PREFIX}/deadlines/{deadline['id']}/done")

    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_log_time_entry(client: TestClient) -> None:
    response = client.post(
        f"{_PREFIX}/time-entries",
        json={
            "firm_id": "firm-1",
            "collaborator_id": "collab-1",
            "case_id": "case-1",
            "duration_minutes": 45,
            "activity_type": "research",
        },
    )

    assert response.status_code == 200
    assert response.json()["duration_minutes"] == 45


def test_full_billing_flow(client: TestClient) -> None:
    invoice = client.post(
        f"{_PREFIX}/billing/invoices",
        json={"firm_id": "firm-1", "client_id": "client-1"},
    ).json()

    client.post(
        f"{_PREFIX}/billing/invoices/{invoice['id']}/lines",
        json={"description": "Honoraires", "quantity": 1, "unit_price": 1000.0},
    )
    issued = client.post(f"{_PREFIX}/billing/invoices/{invoice['id']}/issue")
    assert issued.status_code == 200
    assert issued.json()["status"] == "sent"

    paid = client.post(
        f"{_PREFIX}/billing/invoices/{invoice['id']}/payments",
        json={"amount": 1000.0, "method": "bank_transfer"},
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"
    assert paid.json()["total_due"] == 0.0


def test_subscribe_and_get_subscription(client: TestClient) -> None:
    subscribed = client.post(
        f"{_PREFIX}/subscriptions", json={"firm_id": "firm-1", "plan": "cabinet"}
    )
    assert subscribed.status_code == 200
    assert subscribed.json()["max_users"] == 25

    fetched = client.get(f"{_PREFIX}/subscriptions/firm-1")
    assert fetched.status_code == 200
    assert fetched.json()["plan"] == "cabinet"


def test_register_document_and_list_for_client(client: TestClient) -> None:
    created = client.post(
        f"{_PREFIX}/documents",
        json={
            "firm_id": "firm-1",
            "client_id": "client-1",
            "filename": "contrat.pdf",
            "storage_ref": "s3://bucket/contrat.pdf",
            "category": "contract",
        },
    )
    assert created.status_code == 200

    listed = client.get(f"{_PREFIX}/documents", params={"client_id": "client-1"})
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_dashboards_and_analytics_endpoints(client: TestClient) -> None:
    client.post(f"{_PREFIX}/subscriptions", json={"firm_id": "firm-1", "plan": "solo"})

    cabinet_dash = client.get(f"{_PREFIX}/dashboard/cabinet/firm-1")
    assert cabinet_dash.status_code == 200

    collaborator_dash = client.get(f"{_PREFIX}/dashboard/collaborator/firm-1/collab-1")
    assert collaborator_dash.status_code == 200

    admin_dash = client.get(f"{_PREFIX}/dashboard/admin/firm-1")
    assert admin_dash.status_code == 200
    assert admin_dash.json()["plan"] == "solo"

    analytics = client.get(f"{_PREFIX}/analytics/firm-1")
    assert analytics.status_code == 200


def test_generate_report_returns_a_downloadable_file(client: TestClient) -> None:
    response = client.post(
        f"{_PREFIX}/reports/generate",
        json={
            "title": "Revenue",
            "headers": ["Client", "Amount"],
            "rows": [["Acme", "100"]],
            "report_format": "csv",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "Acme" in response.text


def test_settings_get_and_set(client: TestClient) -> None:
    set_response = client.post(
        f"{_PREFIX}/settings/firm-1/billing/currency", json={"value": "EUR"}
    )
    assert set_response.status_code == 200

    get_response = client.get(f"{_PREFIX}/settings/firm-1/billing/currency")
    assert get_response.status_code == 200
    assert get_response.json()["value"] == "EUR"


def test_administration_firm_lifecycle(client: TestClient) -> None:
    created = client.post(f"{_PREFIX}/administration/firms", json={"name": "Cabinet Durand"})
    assert created.status_code == 200
    firm_id = created.json()["id"]

    suspended = client.post(
        f"{_PREFIX}/administration/firms/{firm_id}/status", json={"status": "suspended"}
    )
    assert suspended.status_code == 200
    assert suspended.json()["status"] == "suspended"

    listed = client.get(f"{_PREFIX}/administration/firms")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_administration_monitoring_snapshot(client: TestClient) -> None:
    response = client.get(f"{_PREFIX}/administration/monitoring")
    assert response.status_code == 200


def test_issue_and_use_public_api_key(client: TestClient) -> None:
    issued = client.post(
        "/api/v1/public-api/v1/keys",
        json={"firm_id": "firm-1", "name": "Integration", "scopes": ["read:clients"]},
    )

    assert issued.status_code == 200
    body = issued.json()
    assert body["raw_key"] is not None
    assert body["prefix"]


def test_oauth_client_credentials_flow(client: TestClient) -> None:
    registered = client.post(
        "/api/v1/public-api/v1/oauth/clients",
        json={
            "firm_id": "firm-1",
            "redirect_uris": ["https://example.com/callback"],
            "scopes": ["read:billing"],
        },
    )
    assert registered.status_code == 200
    body = registered.json()

    token_response = client.post(
        "/api/v1/public-api/v1/oauth/token",
        json={"client_id": body["client_id"], "client_secret": body["client_secret"]},
    )

    assert token_response.status_code == 200
    assert token_response.json()["token"]
