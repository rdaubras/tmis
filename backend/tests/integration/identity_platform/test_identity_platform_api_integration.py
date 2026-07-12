from fastapi.testclient import TestClient

from tmis.main import app


def test_organization_department_team_lifecycle_via_api() -> None:
    client = TestClient(app)

    org = client.post(
        "/api/v1/identity-platform/organizations",
        json={"firm_id": "firm-api-idp-1", "legal_name": "Cabinet API SA"},
    )
    assert org.status_code == 200
    assert org.json()["status"] == "active"

    fetched = client.get("/api/v1/identity-platform/organizations/firm-api-idp-1")
    assert fetched.status_code == 200
    assert fetched.json()["legal_name"] == "Cabinet API SA"

    department = client.post(
        "/api/v1/identity-platform/departments",
        json={"firm_id": "firm-api-idp-1", "name": "Corporate"},
    ).json()

    team = client.post(
        "/api/v1/identity-platform/teams",
        json={"firm_id": "firm-api-idp-1", "department_id": department["id"], "name": "M&A"},
    )
    assert team.status_code == 200
    assert team.json()["department_id"] == department["id"]

    listed_teams = client.get(
        "/api/v1/identity-platform/teams",
        params={"firm_id": "firm-api-idp-1", "department_id": department["id"]},
    )
    assert len(listed_teams.json()) == 1


def test_role_assignment_and_authorization_check_via_api() -> None:
    client = TestClient(app)

    assigned = client.post(
        "/api/v1/identity-platform/roles",
        json={"firm_id": "firm-api-idp-2", "user_id": "partner-1", "role": "partner"},
    )
    assert assigned.status_code == 200
    assert assigned.json()["roles"] == ["partner"]

    allowed = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": "firm-api-idp-2",
            "user_id": "partner-1",
            "permission": "consultation.validate",
        },
    )
    assert allowed.status_code == 200
    assert allowed.json()["allowed"] is True

    denied = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": "firm-api-idp-2",
            "user_id": "paralegal-without-role",
            "permission": "consultation.validate",
        },
    )
    assert denied.json()["allowed"] is False


def test_policy_can_override_an_rbac_grant_via_api() -> None:
    client = TestClient(app)
    firm_id = "firm-api-idp-3"

    client.post(
        "/api/v1/identity-platform/roles",
        json={"firm_id": firm_id, "user_id": "partner-1", "role": "partner"},
    )

    policy = client.post(
        "/api/v1/identity-platform/policies",
        json={
            "firm_id": firm_id,
            "permission": "export.data",
            "denied_roles": ["partner"],
            "reason": "export interdit ce trimestre",
        },
    )
    assert policy.status_code == 200

    decision = client.post(
        "/api/v1/identity-platform/authorize",
        json={"firm_id": firm_id, "user_id": "partner-1", "permission": "export.data"},
    )
    assert decision.json()["allowed"] is False
    assert decision.json()["reason"] == "export interdit ce trimestre"


def test_device_and_session_lifecycle_via_api() -> None:
    client = TestClient(app)
    firm_id = "firm-api-idp-4"

    device = client.post(
        "/api/v1/identity-platform/devices",
        json={"firm_id": firm_id, "user_id": "user-1", "label": "Laptop"},
    ).json()
    assert device["trust_level"] == "unknown"

    trusted = client.post(
        f"/api/v1/identity-platform/devices/{device['id']}/trust", params={"firm_id": firm_id}
    )
    assert trusted.json()["trust_level"] == "trusted"

    revoked = client.post(
        f"/api/v1/identity-platform/devices/{device['id']}/revoke", params={"firm_id": firm_id}
    )
    assert revoked.json()["trust_level"] == "revoked"


def test_delegation_lifecycle_via_api() -> None:
    client = TestClient(app)
    firm_id = "firm-api-idp-5"

    delegation = client.post(
        "/api/v1/identity-platform/delegations",
        json={
            "firm_id": firm_id,
            "delegator_id": "partner-1",
            "delegate_id": "collab-1",
            "permissions": ["export.data"],
            "ends_at": "2099-01-01T00:00:00+00:00",
        },
    )
    assert delegation.status_code == 200
    delegation_id = delegation.json()["id"]

    listed = client.get("/api/v1/identity-platform/delegations", params={"firm_id": firm_id})
    assert len(listed.json()) == 1

    revoked = client.post(
        f"/api/v1/identity-platform/delegations/{delegation_id}/revoke",
        params={"firm_id": firm_id},
    )
    assert revoked.json()["revoked"] is True

    after_revoke = client.get("/api/v1/identity-platform/delegations", params={"firm_id": firm_id})
    assert len(after_revoke.json()) == 0


def test_secret_manager_never_returns_plaintext_via_api() -> None:
    client = TestClient(app)
    firm_id = "firm-api-idp-6"

    created = client.put(
        "/api/v1/identity-platform/secrets",
        json={"firm_id": firm_id, "key": "crm-key", "plaintext": "top-secret-value"},
    )
    assert created.status_code == 200
    assert "top-secret-value" not in created.text

    listed = client.get("/api/v1/identity-platform/secrets", params={"firm_id": firm_id})
    assert listed.json()[0]["key"] == "crm-key"
    assert "plaintext" not in listed.json()[0]
    assert "encrypted_value" not in listed.json()[0]


def test_dashboard_and_security_events_via_api() -> None:
    client = TestClient(app)
    firm_id = "firm-api-idp-7"

    client.post(
        "/api/v1/identity-platform/devices",
        json={"firm_id": firm_id, "user_id": "user-1", "label": "Phone"},
    )

    dashboard = client.get("/api/v1/identity-platform/dashboard", params={"firm_id": firm_id})
    assert dashboard.status_code == 200
    assert dashboard.json()["firm_id"] == firm_id

    events = client.get("/api/v1/identity-platform/security-events", params={"firm_id": firm_id})
    assert events.status_code == 200
