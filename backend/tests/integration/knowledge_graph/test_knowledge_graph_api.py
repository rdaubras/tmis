"""Integration tests for the Knowledge Graph Federation REST API,
exercising the real FastAPI app end-to-end."""

import pytest
from fastapi.testclient import TestClient

from tmis.knowledge_graph import bootstrap
from tmis.main import app

FIRM = "firm-kg-api"


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """The bootstrap accessors are `lru_cache`d process-wide singletons;
    reset them before each test so state created by one test doesn't
    leak into another."""
    for name in dir(bootstrap):
        candidate = getattr(bootstrap, name)
        if callable(candidate) and hasattr(candidate, "cache_clear"):
            candidate.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_resolve_entity_roundtrip(client: TestClient) -> None:
    response = client.post(
        "/api/v1/knowledge-graph/entity-resolution/resolve",
        json={
            "firm_id": FIRM,
            "requested_by": "user-1",
            "occurrences": [
                {"origin": "case_graph", "node_id": "actor-1", "label": "Jean Dupont"},
                {
                    "origin": "document_knowledge_graph",
                    "node_id": "entity-1",
                    "label": "Jean Dupont",
                },
            ],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmed"
    assert body["confidence"] == 1.0

    get_response = client.get(
        f"/api/v1/knowledge-graph/entity-resolution/{body['id']}", params={"firm_id": FIRM}
    )
    assert get_response.status_code == 200
    assert get_response.json()["id"] == body["id"]


def test_get_unknown_resolved_entity_returns_404(client: TestClient) -> None:
    response = client.get(
        "/api/v1/knowledge-graph/entity-resolution/missing", params={"firm_id": FIRM}
    )
    assert response.status_code == 404


def test_semantic_link_roundtrip(client: TestClient) -> None:
    response = client.post(
        "/api/v1/knowledge-graph/semantic-intelligence/link",
        json={
            "objects": [
                ["obj-1", "contrat de bail commercial"],
                ["obj-2", "contrat de bail commercial"],
            ],
            "similarity_threshold": 0.3,
        },
    )

    assert response.status_code == 200
    links = response.json()
    assert len(links) == 1

    get_response = client.get("/api/v1/knowledge-graph/semantic-intelligence/obj-1")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 1


def test_restrict_and_evaluate_entity_visibility(client: TestClient) -> None:
    restrict_response = client.post(
        "/api/v1/knowledge-graph/governance/restrict-entity-visibility",
        json={
            "firm_id": FIRM,
            "entity_id": "resent-1",
            "required_role": "PARTNER",
            "reason": "donnée sensible",
        },
    )
    assert restrict_response.status_code == 200

    blocked = client.post(
        "/api/v1/knowledge-graph/governance/evaluate-entity-visibility",
        json={
            "firm_id": FIRM,
            "production_id": "prod-1",
            "entity_id": "resent-1",
            "user_role": "ASSOCIATE",
        },
    )
    assert blocked.json()["allowed"] is False

    allowed = client.post(
        "/api/v1/knowledge-graph/governance/evaluate-entity-visibility",
        json={
            "firm_id": FIRM,
            "production_id": "prod-1",
            "entity_id": "resent-1",
            "user_role": "PARTNER",
        },
    )
    assert allowed.json()["allowed"] is True


def test_analytics_snapshot(client: TestClient) -> None:
    response = client.get(f"/api/v1/knowledge-graph/analytics/{FIRM}/snapshot")
    assert response.status_code == 200
    body = response.json()
    assert body["firm_id"] == FIRM
    assert body["graph_coverage"] == 0.0
