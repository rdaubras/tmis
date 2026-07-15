"""Integration tests for Sprint 40: `POST /api/v1/watches`, exposing the real
`WatchAgent` (already real since Sprint 36,
docs/164-architecture-agent-veille.md) as a standalone route — see
docs/167-architecture-exposition-agent-veille.md for the two open questions
this sprint settles (standalone router with an optional `case_id` in the
body, and `POST` over `GET` with list query parameters).

No SQL fixture is needed here (unlike the document/case_intelligence API
tests): `WatchAgent` never touches a `CaseStorePort`/`DocumentStorePort`, it
only calls `ResearchOrchestrator.search()` (Sprint 5), which is entirely
in-memory in this repo's default wiring — the exact same setup already used
by `tests/integration/agents/test_watch_agent_integration.py`.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.legal_research.bootstrap import get_research_orchestrator
from tmis.main import app


@pytest.fixture(autouse=True)
def _clear_singletons() -> None:
    """Same reset as `test_watch_agent_integration.py`: both `WatchAgent`'s
    `ResearchOrchestrator` and the shared `TMISKernel` are `lru_cache`d
    process-wide singletons that must not leak connector registrations or
    research history between tests."""
    get_research_orchestrator.cache_clear()
    get_kernel.cache_clear()
    from tmis.agents.bootstrap import get_watch_agent

    get_watch_agent.cache_clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_watch_with_query_only(client: TestClient) -> None:
    response = client.post(
        "/api/v1/watches", json={"query": "responsabilité contractuelle"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["query"] == "responsabilité contractuelle"
    assert body["result"]["new_results"]
    assert body["result"]["alert_message"]
    assert body["confidence"] in ("low", "medium", "high")
    assert len(body["citations"]) == len(body["result"]["new_results"])


def test_watch_filtered_to_a_connector(client: TestClient) -> None:
    response = client.post(
        "/api/v1/watches",
        json={
            "query": "responsabilité contractuelle",
            "connectors": ["jurisprudence"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["connectors_used"] == ["jurisprudence"]
    for result in body["result"]["new_results"]:
        assert result["connector"] == "jurisprudence"
    for citation in body["citations"]:
        assert citation["connector"] == "jurisprudence"


def test_watch_excludes_already_known_result_ids(client: TestClient) -> None:
    first = client.post(
        "/api/v1/watches",
        json={
            "query": "responsabilité contractuelle",
            "connectors": ["jurisprudence"],
        },
    )
    known_ids = first.json()["result"]["result_ids"]
    assert known_ids

    second = client.post(
        "/api/v1/watches",
        json={
            "query": "responsabilité contractuelle",
            "connectors": ["jurisprudence"],
            "known_result_ids": known_ids,
        },
    )

    assert second.status_code == 200
    body = second.json()
    assert body["result"]["new_results"] == []
    assert body["result"]["alert_message"] is None
    assert body["citations"] == []
    assert any("No new result" in warning for warning in body["warnings"])


def test_watch_with_a_case_id(client: TestClient) -> None:
    case_id = str(uuid.uuid4())

    response = client.post(
        "/api/v1/watches",
        json={"query": "clause de non-concurrence", "case_id": case_id},
    )

    assert response.status_code == 200
    orchestrator = get_research_orchestrator()
    entries = orchestrator.history.list_for_case(case_id)
    assert len(entries) == 1
    assert entries[0].query_text == "clause de non-concurrence"


def test_watch_without_a_case_id(client: TestClient) -> None:
    response = client.post(
        "/api/v1/watches", json={"query": "clause de non-concurrence"}
    )

    assert response.status_code == 200


def test_watch_rejects_a_request_without_a_query(client: TestClient) -> None:
    response = client.post("/api/v1/watches", json={})

    assert response.status_code == 422
