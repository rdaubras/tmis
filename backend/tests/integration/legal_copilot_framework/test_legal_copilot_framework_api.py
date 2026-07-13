"""Integration tests for the Legal Copilot Framework REST API, exercising
the real FastAPI app and the Enterprise Identity & Trust Platform gate
(see `identity_platform.api.guard.authorize_or_403`)."""

from fastapi.testclient import TestClient

from tmis.identity_platform.bootstrap import get_role_engine
from tmis.identity_platform.roles.schemas import Role
from tmis.main import app

FIRM = "firm-lcf-api"


def _authorized_user(user_id: str = "partner-lcf") -> str:
    get_role_engine().assign(FIRM, user_id, Role.PARTNER)
    return user_id


def test_register_copilot_requires_authorization() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/v1/legal-copilots/register",
        json={
            "firm_id": FIRM,
            "user_id": "unauthorized-user",
            "id": "copilot-unauthorized",
            "name": "Copilote",
            "domain": "civil",
            "description": "desc",
            "version": "1.0.0",
        },
    )

    assert response.status_code == 403


def test_register_get_and_list_copilot_roundtrip() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    registered = client.post(
        "/api/v1/legal-copilots/register",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "id": "copilot-api-1",
            "name": "Copilote API",
            "domain": "civil",
            "description": "desc",
            "version": "1.0.0",
        },
    )
    assert registered.status_code == 200
    body = registered.json()
    assert body["id"] == "copilot-api-1"
    assert body["status"] == "draft"

    fetched = client.get("/api/v1/legal-copilots/copilot-api-1")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Copilote API"

    listed = client.get("/api/v1/legal-copilots")
    assert listed.status_code == 200
    assert any(c["id"] == "copilot-api-1" for c in listed.json())

    versions = client.get("/api/v1/legal-copilots/copilot-api-1/versions")
    assert versions.status_code == 200
    assert [v["version"] for v in versions.json()] == ["1.0.0"]


def test_get_unknown_copilot_returns_404() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/legal-copilots/does-not-exist")

    assert response.status_code == 404


def test_register_with_unresolvable_pack_reference_returns_422() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    response = client.post(
        "/api/v1/legal-copilots/register",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "id": "copilot-api-invalid",
            "name": "Copilote invalide",
            "domain": "civil",
            "description": "desc",
            "version": "1.0.0",
            "prompt_pack_id": "does-not-exist",
        },
    )

    assert response.status_code == 422


def test_install_then_deactivate_copilot() -> None:
    client = TestClient(app)
    user_id = _authorized_user()
    client.post(
        "/api/v1/legal-copilots/register",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "id": "copilot-api-lifecycle",
            "name": "Copilote lifecycle",
            "domain": "civil",
            "description": "desc",
            "version": "1.0.0",
        },
    )

    installed = client.post(
        "/api/v1/legal-copilots/copilot-api-lifecycle/install",
        json={"firm_id": FIRM, "user_id": user_id},
    )
    assert installed.status_code == 200
    assert installed.json()["active"] is True

    deactivated = client.post(
        "/api/v1/legal-copilots/copilot-api-lifecycle/deactivate",
        json={"firm_id": FIRM, "user_id": user_id},
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False


def test_publish_prompt_pack_and_reference_it_from_a_copilot() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    published = client.post(
        "/api/v1/legal-copilots/packs/prompt",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "id": "pp-api-1",
            "name": "Prompts API",
            "domain": "civil",
        },
    )
    assert published.status_code == 200
    assert published.json()["version"] == 1

    registered = client.post(
        "/api/v1/legal-copilots/register",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "id": "copilot-api-with-pack",
            "name": "Copilote avec pack",
            "domain": "civil",
            "description": "desc",
            "version": "1.0.0",
            "prompt_pack_id": "pp-api-1",
        },
    )
    assert registered.status_code == 200
    assert registered.json()["prompt_pack_id"] == "pp-api-1"


def test_publish_pack_with_unknown_domain_returns_422() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    response = client.post(
        "/api/v1/legal-copilots/packs/knowledge",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "id": "kp-api-invalid",
            "name": "Pack",
            "domain": "not-a-real-domain",
        },
    )

    assert response.status_code == 422


def test_get_metrics_for_unused_copilot_is_zeroed() -> None:
    client = TestClient(app)
    user_id = _authorized_user()
    client.post(
        "/api/v1/legal-copilots/register",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "id": "copilot-api-metrics",
            "name": "Copilote metrics",
            "domain": "civil",
            "description": "desc",
            "version": "1.0.0",
        },
    )

    response = client.get(
        "/api/v1/legal-copilots/copilot-api-metrics/metrics",
        params={"firm_id": FIRM, "user_id": user_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["copilot_id"] == "copilot-api-metrics"
    assert body["usage_count"] == 0


def test_seed_demo_copilots_is_idempotent_and_populates_the_registry() -> None:
    client = TestClient(app)
    user_id = _authorized_user()

    seed_body = {"firm_id": FIRM, "user_id": user_id}
    first = client.post("/api/v1/legal-copilots/demo/seed", json=seed_body)
    assert first.status_code == 200
    copilot_ids = first.json()["copilot_ids"]
    assert len(copilot_ids) == 5

    second = client.post("/api/v1/legal-copilots/demo/seed", json=seed_body)
    assert second.status_code == 200
    assert second.json()["copilot_ids"] == copilot_ids

    listed = client.get("/api/v1/legal-copilots")
    listed_ids = {c["id"] for c in listed.json()}
    assert set(copilot_ids).issubset(listed_ids)


def test_publish_to_marketplace_makes_the_copilot_a_published_plugin() -> None:
    client = TestClient(app)
    user_id = _authorized_user()
    client.post(
        "/api/v1/legal-copilots/register",
        json={
            "firm_id": FIRM,
            "user_id": user_id,
            "id": "copilot-api-marketplace",
            "name": "Copilote marketplace",
            "domain": "civil",
            "description": "desc",
            "version": "1.0.0",
        },
    )

    published = client.post(
        "/api/v1/legal-copilots/copilot-api-marketplace/publish-to-marketplace",
        json={"firm_id": FIRM, "user_id": user_id},
    )

    assert published.status_code == 200
    body = published.json()
    assert body["plugin_id"] == "copilot-api-marketplace"
    assert body["plugin_type"] == "copilot"
    assert body["status"] == "published"
    assert body["signature"] is not None
