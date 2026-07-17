import pytest
from fastapi.testclient import TestClient

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import clear_case_intelligence_caches
from tmis.legal_reasoning.bootstrap import get_reasoning_orchestrator
from tmis.legal_research.bootstrap import clear_research_caches
from tmis.main import app


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    get_reasoning_orchestrator.cache_clear()
    clear_research_caches()
    clear_case_intelligence_caches()
    get_kernel.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_launch_reasoning_returns_a_full_session(client: TestClient) -> None:
    response = client.post(
        "/api/v1/legal-reasoning/reason",
        json={"question": "Le contrat de travail peut-il être rompu ?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["hypotheses"]) == 2
    assert body["synthesis"]
    assert body["decision_graph"]["nodes"]


def test_get_session_retrieves_a_previous_reasoning_run(client: TestClient) -> None:
    created = client.post(
        "/api/v1/legal-reasoning/reason",
        json={"question": "Le contrat de travail peut-il être rompu ?"},
    ).json()

    response = client.get(f"/api/v1/legal-reasoning/sessions/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_session_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/api/v1/legal-reasoning/sessions/does-not-exist")
    assert response.status_code == 404


def test_get_hypotheses_endpoint(client: TestClient) -> None:
    created = client.post(
        "/api/v1/legal-reasoning/reason",
        json={"question": "Le contrat de travail peut-il être rompu ?"},
    ).json()

    response = client.get(f"/api/v1/legal-reasoning/sessions/{created['id']}/hypotheses")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_arguments_endpoint(client: TestClient) -> None:
    created = client.post(
        "/api/v1/legal-reasoning/reason",
        json={"question": "Le contrat de travail peut-il être rompu ?"},
    ).json()

    response = client.get(f"/api/v1/legal-reasoning/sessions/{created['id']}/arguments")

    assert response.status_code == 200


def test_get_conflicts_endpoint_returns_empty_list_without_a_case(client: TestClient) -> None:
    created = client.post(
        "/api/v1/legal-reasoning/reason",
        json={"question": "Le contrat de travail peut-il être rompu ?"},
    ).json()

    response = client.get(f"/api/v1/legal-reasoning/sessions/{created['id']}/conflicts")

    assert response.status_code == 200
    assert response.json() == []


def test_get_synthesis_endpoint(client: TestClient) -> None:
    created = client.post(
        "/api/v1/legal-reasoning/reason",
        json={"question": "Le contrat de travail peut-il être rompu ?"},
    ).json()

    response = client.get(f"/api/v1/legal-reasoning/sessions/{created['id']}/synthesis")

    assert response.status_code == 200
    assert response.json()["synthesis"] == created["synthesis"]
