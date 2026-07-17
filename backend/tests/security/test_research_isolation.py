"""Isolation tests for the "legal_research" persistent & isolated slice
(docs/21-legal-research.md, ADR-RESEARCH-01/02). Talks to the real app
through `authenticated_session` (real, signed JWTs via `/auth/login`) —
nothing here bypasses the auth boundary, matching every other test in
this directory (see `tests/security/test_drafting_isolation.py`, the
`cases -> drafting` slice's own suite, which this one mirrors).
"""

import uuid
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

import tmis.legal_research.history.adapters.sqlalchemy_store  # noqa: F401 — registers research_history_entries
import tmis.legal_research.search.sqlalchemy_store  # noqa: F401 — registers research_searches
from tmis.core.database import SessionLocal
from tmis.legal_research.bootstrap import get_research_orchestrator

_PRIVATE_QUERY = "non-concurrence"
_PRIVATE_CONNECTORS = ["private_database"]


def _create_case(session: Any, title: str = "Dossier") -> str:
    response = session.client.post("/api/v1/cases", json={"title": title})
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _launch_search(session: Any, **overrides: object) -> dict[str, Any]:
    payload: dict[str, object] = {"query": "contrat de travail", "connector_names": ["codes"]}
    payload.update(overrides)
    response = session.client.post("/api/v1/legal-research/search", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_firm_b_gets_404_reading_firm_a_search(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    search = _launch_search(firm_a)

    response = firm_b.client.get(f"/api/v1/legal-research/searches/{search['search_id']}")
    assert response.status_code == 404

    ok = firm_a.client.get(f"/api/v1/legal-research/searches/{search['search_id']}")
    assert ok.status_code == 200


def test_isolation_is_symmetric(authenticated_session: Callable[..., Any]) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    search_a = _launch_search(firm_a)
    search_b = _launch_search(firm_b)

    assert (
        firm_a.client.get(f"/api/v1/legal-research/searches/{search_b['search_id']}").status_code
        == 404
    )
    assert (
        firm_b.client.get(f"/api/v1/legal-research/searches/{search_a['search_id']}").status_code
        == 404
    )


def test_launch_search_with_another_firms_case_id_returns_404_and_creates_nothing(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier confidentiel A")

    response = firm_b.client.post(
        "/api/v1/legal-research/search",
        json={"query": "contrat de travail", "connector_names": ["codes"], "case_id": case_a},
    )
    assert response.status_code == 404
    assert "confidentiel" not in response.text


def test_launch_search_with_own_firms_case_id_succeeds(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    case_a = _create_case(firm_a, "Dossier A")

    search = _launch_search(firm_a, case_id=case_a)
    assert search["search_id"]


def test_launch_search_with_malformed_case_id_returns_404(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")

    response = firm_a.client.post(
        "/api/v1/legal-research/search",
        json={"query": "contrat de travail", "connector_names": ["codes"], "case_id": "not-a-uuid"},
    )
    assert response.status_code == 404


def test_history_isolation(authenticated_session: Callable[..., Any]) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    _launch_search(firm_a)

    own = firm_a.client.get("/api/v1/legal-research/history")
    assert own.status_code == 200 and own.json()

    other = firm_b.client.get("/api/v1/legal-research/history")
    assert other.status_code == 200
    assert other.json() == []


def test_history_by_case_id_returns_404_for_another_firms_case(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier confidentiel A")
    _launch_search(firm_a, case_id=case_a)

    response = firm_b.client.get("/api/v1/legal-research/history", params={"case_id": case_a})
    assert response.status_code == 404


def test_two_firms_in_the_same_process_share_no_search_state(
    authenticated_session: Callable[..., Any],
) -> None:
    """Non-regression for the singleton this slice removed
    (ADR-RESEARCH-02): two firms, same process, no `dependency_overrides`
    — if `get_research_orchestrator` were still an `lru_cache` singleton
    carrying one shared store, firm B would be able to read firm A's
    search through its own orchestrator instance."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    search_a = _launch_search(firm_a)

    with SessionLocal() as session:
        orchestrator_a = get_research_orchestrator(session=session, firm_id=firm_a.user.firm_id)
        orchestrator_b = get_research_orchestrator(session=session, firm_id=firm_b.user.firm_id)

        assert orchestrator_a.get_response(search_a["search_id"]) is not None
        assert orchestrator_b.get_response(search_a["search_id"]) is None


def test_search_persists_across_a_brand_new_session_and_store_instance(
    authenticated_session: Callable[..., Any],
) -> None:
    """Persistence-survives-restart: build a fresh `Session` and a fresh
    orchestrator (never the object that created the search) and confirm
    the search is still there, scoped to the right firm — the same
    guarantee `cases`/`drafting_documents` already have."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    search = _launch_search(firm_a)

    with SessionLocal() as fresh_session:
        fresh_orchestrator = get_research_orchestrator(
            session=fresh_session, firm_id=firm_a.user.firm_id
        )
        reloaded = fresh_orchestrator.get_response(search["search_id"])
        assert reloaded is not None
        assert reloaded.search_id == search["search_id"]
        assert fresh_orchestrator.get_citations(search["search_id"]) is not None

    with SessionLocal() as other_firm_session:
        other_orchestrator = get_research_orchestrator(
            session=other_firm_session, firm_id=uuid.uuid4()
        )
        assert other_orchestrator.get_response(search["search_id"]) is None


def test_cache_does_not_leak_a_private_connectors_results_across_firms(
    authenticated_session: Callable[..., Any],
) -> None:
    """ADR-RESEARCH-01 (docs/21-legal-research.md): the cache is the real
    trap in this module — a raw-search cache entry keyed only by
    `(search_text, connector_names)` would let firm B's identical query
    return firm A's cached `private_database` results on the second hit.
    `firm_id` is prefixed into every cache key precisely so this cannot
    happen: firm A's second identical search hits its own cache; firm
    B's first identical search does not — it must reach the connector
    itself, same as firm A's first one did."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    first_a = _launch_search(firm_a, query=_PRIVATE_QUERY, connector_names=_PRIVATE_CONNECTORS)
    assert first_a["cache_hit"] is False

    second_a = _launch_search(firm_a, query=_PRIVATE_QUERY, connector_names=_PRIVATE_CONNECTORS)
    assert second_a["cache_hit"] is True

    first_b = _launch_search(firm_b, query=_PRIVATE_QUERY, connector_names=_PRIVATE_CONNECTORS)
    assert first_b["cache_hit"] is False


def _research_get_paths_with_search_id(app_under_test: FastAPI, search_id: str) -> list[str]:
    prefix = "/api/v1/legal-research"
    return [
        route.path.replace("{search_id}", search_id)
        for route in app_under_test.routes
        if getattr(route, "path", "").startswith(prefix)
        and "{search_id}" in getattr(route, "path", "")
        and "GET" in (getattr(route, "methods", None) or set())
    ]


def test_no_research_get_route_leaks_across_firms(
    authenticated_session: Callable[..., Any], app_under_test: FastAPI
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")
    search = _launch_search(firm_a)

    paths = _research_get_paths_with_search_id(app_under_test, search["search_id"])
    assert paths, "le walk de routes ne doit pas être vide"
    for path in paths:
        assert firm_b.client.get(path).status_code == 404, f"{path} fuit cross-firm"
