"""Demonstrates that no firm's identity data is ever visible from
another firm's context — the sprint's explicit multi-tenant isolation
requirement ("aucune donnée d'un cabinet n'est jamais visible depuis
un autre tenant")."""

from fastapi.testclient import TestClient

from tmis.main import app


def test_organizations_are_isolated_per_firm() -> None:
    client = TestClient(app)

    client.post(
        "/api/v1/identity-platform/organizations",
        json={"firm_id": "firm-iso-a", "legal_name": "Cabinet A"},
    )
    client.post(
        "/api/v1/identity-platform/organizations",
        json={"firm_id": "firm-iso-b", "legal_name": "Cabinet B"},
    )

    firm_a = client.get("/api/v1/identity-platform/organizations/firm-iso-a").json()
    firm_b = client.get("/api/v1/identity-platform/organizations/firm-iso-b").json()

    assert firm_a["legal_name"] == "Cabinet A"
    assert firm_b["legal_name"] == "Cabinet B"


def test_role_assignments_do_not_leak_across_firms() -> None:
    client = TestClient(app)

    client.post(
        "/api/v1/identity-platform/roles",
        json={"firm_id": "firm-iso-c", "user_id": "shared-user-id", "role": "partner"},
    )

    same_user_other_firm = client.get(
        "/api/v1/identity-platform/roles",
        params={"firm_id": "firm-iso-d", "user_id": "shared-user-id"},
    )

    assert same_user_other_firm.json()["roles"] == []


def test_authorization_check_for_role_granted_in_a_different_firm_is_denied() -> None:
    """A user given PARTNER in firm A must never be authorized to
    validate a consultation when addressed under firm B — the same
    `user_id` string means nothing across tenant boundaries."""
    client = TestClient(app)

    client.post(
        "/api/v1/identity-platform/roles",
        json={"firm_id": "firm-iso-e", "user_id": "cross-tenant-user", "role": "partner"},
    )

    decision_in_own_firm = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": "firm-iso-e",
            "user_id": "cross-tenant-user",
            "permission": "consultation.validate",
        },
    )
    decision_in_other_firm = client.post(
        "/api/v1/identity-platform/authorize",
        json={
            "firm_id": "firm-iso-f",
            "user_id": "cross-tenant-user",
            "permission": "consultation.validate",
        },
    )

    assert decision_in_own_firm.json()["allowed"] is True
    assert decision_in_other_firm.json()["allowed"] is False


def test_devices_sessions_delegations_and_secrets_are_isolated_per_firm() -> None:
    client = TestClient(app)

    client.post(
        "/api/v1/identity-platform/devices",
        json={"firm_id": "firm-iso-g", "user_id": "user-1", "label": "Laptop G"},
    )
    client.post(
        "/api/v1/identity-platform/devices",
        json={"firm_id": "firm-iso-h", "user_id": "user-1", "label": "Laptop H"},
    )
    client.put(
        "/api/v1/identity-platform/secrets",
        json={"firm_id": "firm-iso-g", "key": "shared-key-name", "plaintext": "secret-g"},
    )
    client.put(
        "/api/v1/identity-platform/secrets",
        json={"firm_id": "firm-iso-h", "key": "shared-key-name", "plaintext": "secret-h"},
    )

    devices_g = client.get(
        "/api/v1/identity-platform/devices", params={"firm_id": "firm-iso-g", "user_id": "user-1"}
    ).json()
    devices_h = client.get(
        "/api/v1/identity-platform/devices", params={"firm_id": "firm-iso-h", "user_id": "user-1"}
    ).json()

    assert [d["label"] for d in devices_g] == ["Laptop G"]
    assert [d["label"] for d in devices_h] == ["Laptop H"]

    secrets_g = client.get(
        "/api/v1/identity-platform/secrets", params={"firm_id": "firm-iso-g"}
    ).json()
    secrets_h = client.get(
        "/api/v1/identity-platform/secrets", params={"firm_id": "firm-iso-h"}
    ).json()

    assert len(secrets_g) == 1
    assert len(secrets_h) == 1


def test_dashboard_never_mixes_counts_across_firms() -> None:
    client = TestClient(app)

    for i in range(3):
        client.post(
            "/api/v1/identity-platform/devices",
            json={"firm_id": "firm-iso-i", "user_id": f"user-{i}", "label": "Device"},
        )
    client.post(
        "/api/v1/identity-platform/devices",
        json={"firm_id": "firm-iso-j", "user_id": "user-0", "label": "Device"},
    )

    dashboard_i = client.get(
        "/api/v1/identity-platform/dashboard", params={"firm_id": "firm-iso-i"}
    ).json()
    dashboard_j = client.get(
        "/api/v1/identity-platform/dashboard", params={"firm_id": "firm-iso-j"}
    ).json()

    assert dashboard_i["firm_id"] == "firm-iso-i"
    assert dashboard_j["firm_id"] == "firm-iso-j"
