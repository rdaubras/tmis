import pytest
from fastapi.testclient import TestClient

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.legal_research.bootstrap import get_research_orchestrator
from tmis.main import app


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    get_research_orchestrator.cache_clear()
    get_kernel.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_launch_search_returns_ranked_results_and_matching_citations(client: TestClient) -> None:
    response = client.post(
        "/api/v1/legal-research/search",
        json={"query": "contrat de travail", "connector_names": ["codes"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["results"]
    assert len(body["results"]) == len(body["citations"])
    assert body["connectors_used"] == ["codes"]


def test_get_search_retrieves_a_previous_search(client: TestClient) -> None:
    created = client.post(
        "/api/v1/legal-research/search",
        json={"query": "contrat de travail", "connector_names": ["codes"]},
    ).json()

    response = client.get(f"/api/v1/legal-research/searches/{created['search_id']}")

    assert response.status_code == 200
    assert response.json()["search_id"] == created["search_id"]


def test_get_search_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/api/v1/legal-research/searches/does-not-exist")
    assert response.status_code == 404


def test_get_history_filters_by_user_id(client: TestClient) -> None:
    client.post(
        "/api/v1/legal-research/search",
        json={"query": "contrat de travail", "connector_names": ["codes"], "user_id": "user-1"},
    )
    client.post(
        "/api/v1/legal-research/search",
        json={"query": "bail", "connector_names": ["codes"], "user_id": "user-2"},
    )

    response = client.get("/api/v1/legal-research/history", params={"user_id": "user-1"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["user_id"] == "user-1"


def test_get_history_without_filters_returns_everything(client: TestClient) -> None:
    client.post(
        "/api/v1/legal-research/search",
        json={"query": "contrat de travail", "connector_names": ["codes"]},
    )

    response = client.get("/api/v1/legal-research/history")

    assert response.status_code == 200
    assert len(response.json()) >= 1
