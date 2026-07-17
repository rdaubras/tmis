"""Isolation tests for the "cases -> drafting" persistent & isolated
slice (docs/28-legal-drafting.md, ADR-SLICE-01/02/03). Talks to the real
app through `authenticated_session` (real, signed JWTs via `/auth/login`)
— nothing here bypasses the auth boundary, matching every other test in
this directory.
"""

import uuid
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

import tmis.legal_drafting.documents.sqlalchemy_store  # noqa: F401 — registers drafting_documents
import tmis.legal_drafting.versioning.sqlalchemy_service  # noqa: F401 — registers versions table
from tmis.core.database import SessionLocal
from tmis.legal_drafting.bootstrap import get_document_orchestrator


def _create_case(session: Any, title: str = "Dossier") -> str:
    response = session.client.post("/api/v1/cases", json={"title": title})
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _create_draft(session: Any, **overrides: object) -> dict[str, Any]:
    payload: dict[str, object] = {"document_type": "consultation"}
    payload.update(overrides)
    response = session.client.post("/api/v1/legal-drafting/drafts", json=payload)
    assert response.status_code == 200, response.text
    return response.json()


def test_firm_b_gets_404_reading_firm_a_draft(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    draft = _create_draft(firm_a)

    response = firm_b.client.get(f"/api/v1/legal-drafting/drafts/{draft['id']}")
    assert response.status_code == 404

    assert firm_a.client.get(f"/api/v1/legal-drafting/drafts/{draft['id']}").status_code == 200


def test_isolation_is_symmetric(authenticated_session: Callable[..., Any]) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    draft_a = _create_draft(firm_a)
    draft_b = _create_draft(firm_b)

    assert firm_a.client.get(f"/api/v1/legal-drafting/drafts/{draft_b['id']}").status_code == 404
    assert firm_b.client.get(f"/api/v1/legal-drafting/drafts/{draft_a['id']}").status_code == 404


def test_firm_b_cannot_regenerate_firm_a_draft(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    draft = _create_draft(firm_a)

    response = firm_b.client.post(
        f"/api/v1/legal-drafting/drafts/{draft['id']}/sections/context/regenerate"
    )
    assert response.status_code == 404

    # Firm A's draft is untouched — same sections, no accidental mutation.
    reread = firm_a.client.get(f"/api/v1/legal-drafting/drafts/{draft['id']}").json()
    assert reread["sections"] == draft["sections"]


def test_create_draft_with_another_firms_case_id_returns_404_and_creates_nothing(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier confidentiel A")

    response = firm_b.client.post(
        "/api/v1/legal-drafting/drafts",
        json={"document_type": "consultation", "case_id": case_a},
    )
    assert response.status_code == 404
    assert "confidentiel" not in response.text


def test_create_draft_with_own_firms_case_id_succeeds(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    case_a = _create_case(firm_a, "Dossier A")

    draft = _create_draft(firm_a, case_id=case_a)
    assert draft["case_id"] == case_a


def test_create_draft_with_malformed_case_id_returns_404(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")

    response = firm_a.client.post(
        "/api/v1/legal-drafting/drafts",
        json={"document_type": "consultation", "case_id": "not-a-uuid"},
    )
    assert response.status_code == 404


def test_version_isolation(authenticated_session: Callable[..., Any]) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    draft = _create_draft(firm_a)
    firm_a.client.post(f"/api/v1/legal-drafting/drafts/{draft['id']}/sections/context/regenerate")

    firm_a_versions = firm_a.client.get(
        f"/api/v1/legal-drafting/drafts/{draft['id']}/versions"
    ).json()
    assert len(firm_a_versions) == 2

    firm_b_versions = firm_b.client.get(
        f"/api/v1/legal-drafting/drafts/{draft['id']}/versions"
    ).json()
    assert firm_b_versions == []


def test_two_firms_in_the_same_process_share_no_draft_state(
    authenticated_session: Callable[..., Any],
) -> None:
    """Non-regression for the singleton this slice removed
    (ADR-SLICE-02): two firms, same process, no `dependency_overrides` —
    if `get_document_orchestrator` were still an `lru_cache` singleton
    carrying one shared store, firm B would be able to read firm A's
    draft through its own orchestrator instance."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    draft_a = _create_draft(firm_a)

    with SessionLocal() as session:
        orchestrator_a = get_document_orchestrator(session=session, firm_id=firm_a.user.firm_id)
        orchestrator_b = get_document_orchestrator(session=session, firm_id=firm_b.user.firm_id)

        assert orchestrator_a.get_document(draft_a["id"]) is not None
        assert orchestrator_b.get_document(draft_a["id"]) is None


def test_history_isolation(authenticated_session: Callable[..., Any]) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    draft = _create_draft(firm_a)

    own = firm_a.client.get(f"/api/v1/legal-drafting/drafts/{draft['id']}/history")
    assert own.status_code == 200 and own.json()  # la création y est déjà enregistrée

    leaked = firm_b.client.get(f"/api/v1/legal-drafting/drafts/{draft['id']}/history")
    assert leaked.status_code == 404


def _drafting_doc_get_paths(app_under_test: FastAPI, draft_id: str) -> list[str]:
    prefix = "/api/v1/legal-drafting/drafts/{document_id}"
    # /versions and /versions/compare are excluded: unlike every other route
    # here they don't go through `_require_document`, but `VersioningPort`
    # is independently firm-scoped at the persistence layer (`scoped_query`
    # in sqlalchemy_service.py), so no content actually leaks — they return
    # 200/[] or 422 (missing required query params) rather than 404. That's
    # a real inconsistency, but a different, lower-severity one than the
    # `history` leak this fix targets, and fixing it is out of scope here
    # (see DoD: report separately, don't expand silently).
    excluded_suffixes = ("/versions", "/versions/compare")
    return [
        route.path.replace("{document_id}", draft_id)
        for route in app_under_test.routes
        if getattr(route, "path", "").startswith(prefix)
        and "GET" in (getattr(route, "methods", None) or set())
        and route.path[len(prefix) :] not in excluded_suffixes
    ]


def test_no_drafting_get_route_leaks_across_firms(
    authenticated_session: Callable[..., Any], app_under_test: FastAPI
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")
    draft = _create_draft(firm_a)

    paths = _drafting_doc_get_paths(app_under_test, draft["id"])
    assert paths, "le walk de routes ne doit pas être vide"
    for path in paths:
        assert firm_b.client.get(path).status_code == 404, f"{path} fuit cross-firm"


def test_draft_persists_across_a_brand_new_session_and_store_instance(
    authenticated_session: Callable[..., Any],
) -> None:
    """Persistence-survives-restart: build a fresh `Session` and a fresh
    orchestrator (never the object that created the draft) and confirm
    the draft is still there, scoped to the right firm — the same
    guarantee `cases` already has."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    draft = _create_draft(firm_a)

    with SessionLocal() as fresh_session:
        fresh_orchestrator = get_document_orchestrator(
            session=fresh_session, firm_id=firm_a.user.firm_id
        )
        reloaded = fresh_orchestrator.get_document(draft["id"])
        assert reloaded is not None
        assert reloaded.id == draft["id"]

    with SessionLocal() as other_firm_session:
        other_orchestrator = get_document_orchestrator(
            session=other_firm_session, firm_id=uuid.uuid4()
        )
        assert other_orchestrator.get_document(draft["id"]) is None
