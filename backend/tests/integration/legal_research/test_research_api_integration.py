import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import tmis.infrastructure.persistence.models  # noqa: F401 — registers firms/users/cases
import tmis.legal_research.history.adapters.sqlalchemy_store  # noqa: F401 — registers research_history_entries
import tmis.legal_research.search.sqlalchemy_store  # noqa: F401 — registers research_searches
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.core import database as core_database
from tmis.legal_research.bootstrap import clear_research_caches
from tmis.main import app


@pytest.fixture(autouse=True)
def _clear_singletons(tmp_path: object) -> None:
    """Points the shared sync engine at a throwaway sqlite database (same
    pattern as `test_drafting_api_integration.py`) instead of whatever
    `TMIS_DATABASE_URL` happens to be configured to, and resets the
    process-wide singletons `legal_research.bootstrap` still owns
    (ADR-RESEARCH-02, docs/21-legal-research.md — `get_research_
    orchestrator` itself is no longer one of them, it is assembled per
    request)."""
    engine = create_engine(
        f"sqlite:///{tmp_path}/research-api.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_database.SessionLocal.configure(bind=engine)
    core_database.Base.metadata.create_all(engine)

    clear_research_caches()
    get_kernel.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_case(client: TestClient, title: str = "Dossier") -> str:
    response = client.post("/api/v1/cases", json={"title": title})
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


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


def test_get_history_returns_the_current_users_searches(client: TestClient) -> None:
    client.post(
        "/api/v1/legal-research/search",
        json={"query": "contrat de travail", "connector_names": ["codes"]},
    )
    client.post(
        "/api/v1/legal-research/search",
        json={"query": "bail", "connector_names": ["codes"]},
    )

    response = client.get("/api/v1/legal-research/history")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert {e["query_text"] for e in body} == {"contrat de travail", "bail"}


def test_get_history_filters_by_owned_case_id(client: TestClient) -> None:
    case_id = _create_case(client, "Dossier recherche")
    client.post(
        "/api/v1/legal-research/search",
        json={"query": "contrat de travail", "connector_names": ["codes"], "case_id": case_id},
    )
    client.post(
        "/api/v1/legal-research/search",
        json={"query": "bail", "connector_names": ["codes"]},
    )

    response = client.get("/api/v1/legal-research/history", params={"case_id": case_id})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["case_id"] == case_id


def test_get_history_with_unknown_case_id_returns_404(client: TestClient) -> None:
    response = client.get(
        "/api/v1/legal-research/history", params={"case_id": "00000000-0000-0000-0000-000000000000"}
    )
    assert response.status_code == 404


def test_launch_search_with_malformed_case_id_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/legal-research/search",
        json={"query": "contrat de travail", "connector_names": ["codes"], "case_id": "not-a-uuid"},
    )
    assert response.status_code == 404
