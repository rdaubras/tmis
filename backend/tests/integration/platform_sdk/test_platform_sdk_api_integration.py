from fastapi.testclient import TestClient

from tmis.main import app


def _publish(client: TestClient, plugin_id: str) -> None:
    client.post(f"/api/v1/platform-sdk/plugins/{plugin_id}/validate", json={"actor": "dev1"})
    client.post(f"/api/v1/platform-sdk/plugins/{plugin_id}/sign", json={"actor": "dev1"})
    client.post(f"/api/v1/platform-sdk/plugins/{plugin_id}/publish", json={"actor": "dev1"})


def test_get_unknown_plugin_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/platform-sdk/plugins/unknown-plugin")

    assert response.status_code == 404


def test_plugin_lifecycle_via_api() -> None:
    client = TestClient(app)

    get_response = client.get("/api/v1/platform-sdk/plugins/agent-fiscal")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "development"

    validated = client.post(
        "/api/v1/platform-sdk/plugins/agent-fiscal/validate", json={"actor": "dev1"}
    )
    assert validated.status_code == 200
    assert validated.json()["status"] == "validated"

    signed = client.post(
        "/api/v1/platform-sdk/plugins/agent-fiscal/sign", json={"actor": "dev1"}
    )
    assert signed.json()["status"] == "signed"
    assert signed.json()["signature"] is not None

    published = client.post(
        "/api/v1/platform-sdk/plugins/agent-fiscal/publish", json={"actor": "dev1"}
    )
    assert published.json()["status"] == "published"

    history = client.get("/api/v1/platform-sdk/plugins/agent-fiscal/publishing-history")
    assert [e["to_status"] for e in history.json()] == ["validated", "signed", "published"]


def test_sign_before_validate_returns_400() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/platform-sdk/plugins/agent-droit-social/sign", json={"actor": "dev1"}
    )

    assert response.status_code == 400


def test_marketplace_search_and_install_and_reviews() -> None:
    client = TestClient(app)
    _publish(client, "connector-ged")

    search = client.get("/api/v1/platform-sdk/marketplace", params={"query": "GED"})
    assert search.status_code == 200
    assert any(item["manifest"]["id"] == "connector-ged" for item in search.json())

    install = client.post(
        "/api/v1/platform-sdk/marketplace/connector-ged/install",
        json={"firm_id": "firm-api-1", "permissions": ["read_documents"]},
    )
    assert install.status_code == 200
    assert install.json()["status"] == "active"

    extensions = client.get(
        "/api/v1/platform-sdk/extensions", params={"firm_id": "firm-api-1"}
    )
    assert len(extensions.json()) == 1

    review = client.post(
        "/api/v1/platform-sdk/marketplace/connector-ged/reviews",
        json={"firm_id": "firm-api-1", "rating": 5, "comment": "Très utile"},
    )
    assert review.status_code == 200

    reviews = client.get("/api/v1/platform-sdk/marketplace/connector-ged/reviews")
    assert len(reviews.json()) == 1

    update = client.post(
        "/api/v1/platform-sdk/marketplace/connector-ged/update",
        params={"firm_id": "firm-api-1"},
    )
    assert update.status_code == 200

    uninstall = client.post(
        "/api/v1/platform-sdk/marketplace/connector-ged/uninstall",
        params={"firm_id": "firm-api-1"},
    )
    assert uninstall.status_code == 200
    assert uninstall.json()["status"] == "uninstalled"


def test_install_without_publishing_returns_400() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/platform-sdk/marketplace/document-template-consultation/install",
        json={"firm_id": "firm-api-2", "permissions": []},
    )

    assert response.status_code == 400


def test_developer_portal_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/platform-sdk/developer-portal")

    assert response.status_code == 200
    assert len(response.json()) > 0

    filtered = client.get(
        "/api/v1/platform-sdk/developer-portal", params={"type": "example"}
    )
    assert all(r["type"] == "example" for r in filtered.json())


def test_marketplace_categories_endpoint() -> None:
    client = TestClient(app)
    _publish(client, "agent-fiscal")

    response = client.get("/api/v1/platform-sdk/marketplace/categories")

    assert response.status_code == 200
    assert "agent" in response.json()
