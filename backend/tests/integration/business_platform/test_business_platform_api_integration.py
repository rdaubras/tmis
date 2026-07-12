"""End-to-end REST API smoke test for the SaaS Business Platform —
exercises `business_platform.api.routes` through the full FastAPI
app, including the EITP authorization guard on mutating endpoints
(see `identity_platform.api.guard.authorize_or_403`)."""

from fastapi.testclient import TestClient

from tmis.identity_platform.bootstrap import get_role_engine
from tmis.identity_platform.roles.schemas import Role
from tmis.main import app


def test_plans_endpoint_lists_the_five_default_plans() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/business-platform/plans")

    assert response.status_code == 200
    names = {plan["name"] for plan in response.json()}
    assert names == {"trial", "basic", "professional", "business", "enterprise"}


def test_activate_subscription_requires_authorization() -> None:
    client = TestClient(app)
    firm_id = "firm-api-unauthorized"
    plan_id = client.get("/api/v1/business-platform/plans").json()[0]["id"]
    client.post(
        "/api/v1/business-platform/subscriptions/trial",
        json={"firm_id": firm_id, "plan_id": plan_id},
    )

    response = client.post(
        f"/api/v1/business-platform/subscriptions/{firm_id}/activate",
        json={"user_id": "unauthorized-user"},
    )

    assert response.status_code == 403


def test_authorized_partner_can_activate_subscription_and_assign_a_license() -> None:
    client = TestClient(app)
    firm_id = "firm-api-authorized"
    user_id = "partner-1"
    get_role_engine().assign(firm_id, user_id, Role.PARTNER)

    plans = client.get("/api/v1/business-platform/plans").json()
    professional = next(p for p in plans if p["name"] == "professional")
    client.post(
        "/api/v1/business-platform/subscriptions/trial",
        json={"firm_id": firm_id, "plan_id": professional["id"]},
    )

    activated = client.post(
        f"/api/v1/business-platform/subscriptions/{firm_id}/activate",
        json={"user_id": user_id, "billing_cycle": "monthly"},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"

    license_response = client.post(
        f"/api/v1/business-platform/licenses/{firm_id}/assign",
        json={"user_id": user_id, "license_type": "nominative", "holder_id": user_id},
    )
    assert license_response.status_code == 200
    assert license_response.json()["revoked"] is False

    usage = client.get(f"/api/v1/business-platform/usage/{firm_id}")
    assert usage.status_code == 200
    assert len(usage.json()) > 0

    analytics = client.get(f"/api/v1/business-platform/analytics/{firm_id}")
    assert analytics.status_code == 200
    assert analytics.json()["plan_name"] == "professional"

    portal = client.get(f"/api/v1/business-platform/customer-portal/{firm_id}")
    assert portal.status_code == 200
    assert portal.json()["license_count"] == 1


def test_tenant_settings_get_and_update_roundtrip() -> None:
    client = TestClient(app)
    firm_id = "firm-api-settings"

    defaults = client.get(f"/api/v1/business-platform/tenant-settings/{firm_id}")
    assert defaults.json()["currency"] == "EUR"

    updated = client.put(
        f"/api/v1/business-platform/tenant-settings/{firm_id}", json={"currency": "USD"}
    )
    assert updated.status_code == 200
    assert updated.json()["currency"] == "USD"
