"""Isolation tests for the "case_intelligence" persistent & isolated
slice (docs/19-case-intelligence.md, ADR-CASEINT-01/02/03). Talks to the
real app through `authenticated_session` (real, signed JWTs via
`/auth/login`) — nothing here bypasses the auth boundary, matching every
other test in this directory (see `tests/security/test_drafting_
isolation.py`/`test_research_isolation.py`, which this one mirrors).

Unlike those two slices, `case_intelligence` has three write paths, not
one: the HTTP routes, the Celery task (`trigger_case_workflow_task`) and
the `DocumentProcessed` domain event. The task/event tests below invoke
those paths directly — not only through HTTP — because a suite that only
exercises the routes would pass even if the async paths still leaked
(see docs/19-case-intelligence.md § Points de vigilance).
"""

import asyncio
import uuid
from collections.abc import Callable
from typing import Any

import pytest
from fastapi import FastAPI

import tmis.case_intelligence.cases.adapters.sqlalchemy_store  # noqa: F401 — registers case_profiles
import tmis.document_intelligence.adapters.sqlalchemy_store  # noqa: F401 — registers document_records
from tmis.ai.events.events import DocumentProcessed
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import (
    clear_case_intelligence_caches,
    get_case_graph,
    get_case_store,
    get_shared_case_intelligence_workflow,
)
from tmis.core.database import SessionLocal
from tmis.core.tasks.case_tasks import trigger_case_workflow_task
from tmis.document_intelligence.adapters.sqlalchemy_store import SQLAlchemyDocumentStore
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.record import DocumentRecord

_CONTRACT_TEXT = (
    "CONTRAT DE BAIL COMMERCIAL\n\n"
    "Signé le 12 janvier 2019 par Maître Jean Dupont et la société ACME SARL."
)


@pytest.fixture(autouse=True)
def _clear_kernel_and_case_intelligence_caches() -> None:
    """`get_kernel()` and `case_intelligence.bootstrap`'s accessors are
    process-wide `lru_cache` singletons shared across the whole test
    suite, not just this file. `_register_document_processed_handler`
    (docs/19-case-intelligence.md) subscribes exactly once, lazily, onto
    whichever `EventBus` `get_kernel()` returns *at that moment* — if an
    earlier test file left a stale cached registration pointing at a
    now-replaced kernel's `EventBus` (because that file reset `get_
    kernel` afterwards without also resetting this module's own caches),
    the event tests below would publish onto a fresh bus nobody is
    listening on. Clearing both together, here, guarantees this file's
    own tests always register on the kernel they themselves resolve."""
    get_kernel.cache_clear()
    clear_case_intelligence_caches()


def _create_case(session: Any, title: str = "Dossier") -> str:
    response = session.client.post("/api/v1/cases", json={"title": title})
    assert response.status_code == 201, response.text
    return str(response.json()["id"])


def _create_profile(session: Any, case_id: str, title: str = "Dossier") -> dict[str, Any]:
    response = session.client.post(f"/api/v1/cases/{case_id}/profile", json={"title": title})
    assert response.status_code == 201, response.text
    return response.json()


def _publish_document_processed(**kwargs: Any) -> None:
    """`case_intelligence.bootstrap._register_document_processed_handler`
    subscribes lazily, on first call to `get_case_intelligence_workflow`/
    `get_shared_case_intelligence_workflow` (docs/19-case-intelligence.md)
    — in real deployment some route always calls one of those before the
    first `DocumentProcessed` event fires, but a test that only exercises
    the plain `cases` API (`_create_case`) never touches either, so the
    subscription would never exist and a "no-op" would be indistinguishable
    from a correctly-rejecting handler. Calling this once, explicitly,
    before publishing removes that ambiguity."""
    get_shared_case_intelligence_workflow()
    kernel = get_kernel()
    asyncio.run(kernel.event_bus.publish(DocumentProcessed(**kwargs)))


def _seed_processed_document(document_id: str | None = None) -> str:
    """Persists a `PROCESSED` `DocumentRecord` directly through the real
    `SQLAlchemyDocumentStore`, bypassing the upload API/Celery task —
    the task/event isolation tests below only need a document to exist,
    not a full pipeline run."""
    document_id = document_id or str(uuid.uuid4())
    SQLAlchemyDocumentStore().save(
        DocumentRecord(
            document_id=document_id,
            filename="bail.txt",
            status=ProcessingStatus.PROCESSED,
            raw_bytes=_CONTRACT_TEXT.encode(),
            ocr_text=_CONTRACT_TEXT,
        )
    )
    return document_id


def test_firm_b_gets_404_reading_firm_a_profile(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier confidentiel A")
    _create_profile(firm_a, case_a, "Dossier confidentiel A")

    response = firm_b.client.get(f"/api/v1/cases/{case_a}/profile")
    assert response.status_code == 404
    assert "confidentiel" not in response.text

    ok = firm_a.client.get(f"/api/v1/cases/{case_a}/profile")
    assert ok.status_code == 200


def test_isolation_is_symmetric(authenticated_session: Callable[..., Any]) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier A")
    case_b = _create_case(firm_b, "Dossier B")
    _create_profile(firm_a, case_a)
    _create_profile(firm_b, case_b)

    assert firm_a.client.get(f"/api/v1/cases/{case_b}/profile").status_code == 404
    assert firm_b.client.get(f"/api/v1/cases/{case_a}/profile").status_code == 404


def test_firm_b_cannot_write_firm_as_profile(authenticated_session: Callable[..., Any]) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier A")
    _create_profile(firm_a, case_a, "Titre original")

    response = firm_b.client.patch(f"/api/v1/cases/{case_a}/profile", json={"title": "Piraté"})
    assert response.status_code == 404

    reread = firm_a.client.get(f"/api/v1/cases/{case_a}/profile").json()
    assert reread["title"] == "Titre original"


def test_create_profile_with_another_firms_case_id_returns_404_and_creates_nothing(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier confidentiel A")

    response = firm_b.client.post(
        f"/api/v1/cases/{case_a}/profile", json={"title": "Tentative"}
    )
    assert response.status_code == 404

    # Not even created for firm A under some other implicit title.
    own = firm_a.client.get(f"/api/v1/cases/{case_a}/profile")
    assert own.status_code == 404


def test_create_profile_with_unowned_case_id_returns_404(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")

    response = firm_a.client.post(
        f"/api/v1/cases/{uuid.uuid4()}/profile", json={"title": "Fantome"}
    )
    assert response.status_code == 404


def test_create_profile_with_malformed_case_id_returns_404(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")

    response = firm_a.client.post("/api/v1/cases/not-a-uuid/profile", json={"title": "X"})
    assert response.status_code == 404


def test_trigger_case_workflow_task_rejects_a_case_owned_by_another_firm(
    authenticated_session: Callable[..., Any],
) -> None:
    """T4/T5 (docs/19-case-intelligence.md): the Celery task is invoked
    directly (as a worker would call it), with firm B's `firm_id` and
    firm A's `case_id` — this must be rejected before anything is
    written, not just refused at the HTTP boundary."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier confidentiel A")
    document_id = _seed_processed_document()

    result = trigger_case_workflow_task(str(firm_b.user.firm_id), case_a, document_id)

    assert result is None
    assert get_case_store(firm_a.user.firm_id).get(case_a) is None
    assert get_case_store(firm_b.user.firm_id).get(case_a) is None


def test_trigger_case_workflow_task_for_the_owning_firm_succeeds(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    case_a = _create_case(firm_a, "Dossier A")
    document_id = _seed_processed_document()

    result = trigger_case_workflow_task(str(firm_a.user.firm_id), case_a, document_id)

    assert result == case_a
    profile = get_case_store(firm_a.user.firm_id).get(case_a)
    assert profile is not None
    assert document_id in profile.document_ids


def test_trigger_case_workflow_task_rejects_a_malformed_case_id(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    document_id = _seed_processed_document()

    result = trigger_case_workflow_task(str(firm_a.user.firm_id), "not-a-uuid", document_id)

    assert result is None


def test_document_processed_event_rejects_a_case_owned_by_another_firm(
    authenticated_session: Callable[..., Any],
) -> None:
    """T4 (docs/19-case-intelligence.md): the event handler that replaces
    the auto-`ingest_document` subscription must apply the same
    appartenance check as the HTTP routes and the Celery task — a
    `DocumentProcessed` event carrying firm B's `firm_id` alongside firm
    A's `case_id` must not enrich anything."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier confidentiel A")
    document_id = _seed_processed_document()

    _publish_document_processed(
        workflow_id=uuid.uuid4(),
        document_id=document_id,
        success=True,
        case_id=case_a,
        firm_id=str(firm_b.user.firm_id),
    )

    assert get_case_store(firm_a.user.firm_id).get(case_a) is None
    assert get_case_store(firm_b.user.firm_id).get(case_a) is None


def test_document_processed_event_without_firm_id_enriches_nothing(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    case_a = _create_case(firm_a, "Dossier A")
    document_id = _seed_processed_document()

    _publish_document_processed(
        workflow_id=uuid.uuid4(),
        document_id=document_id,
        success=True,
        case_id=case_a,
        firm_id=None,
    )

    assert get_case_store(firm_a.user.firm_id).get(case_a) is None


def test_document_processed_event_for_the_owning_firm_enriches_the_case(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    case_a = _create_case(firm_a, "Dossier A")
    document_id = _seed_processed_document()

    _publish_document_processed(
        workflow_id=uuid.uuid4(),
        document_id=document_id,
        success=True,
        case_id=case_a,
        firm_id=str(firm_a.user.firm_id),
    )

    profile = get_case_store(firm_a.user.firm_id).get(case_a)
    assert profile is not None
    assert document_id in profile.document_ids


def test_relationship_graph_is_partitioned_per_firm(
    authenticated_session: Callable[..., Any],
) -> None:
    """T3 (docs/19-case-intelligence.md): the knowledge graph a firm's
    documents populate must never be visible from another firm's
    partition — `get_case_graph` is the accessor every write/read path
    goes through, so this asserts on it directly (there is no dedicated
    HTTP route exposing the raw graph yet)."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier A")
    document_id = _seed_processed_document()
    trigger_case_workflow_task(str(firm_a.user.firm_id), case_a, document_id)

    graph_a = get_case_graph(firm_a.user.firm_id)
    graph_b = get_case_graph(firm_b.user.firm_id)

    document_node_id = f"document::{document_id}"
    assert graph_a.get_node(document_node_id) is not None
    assert graph_b.get_node(document_node_id) is None


def test_case_store_persists_across_a_brand_new_session_and_store_instance(
    authenticated_session: Callable[..., Any],
) -> None:
    """Persistence-survives-restart: a fresh `SQLAlchemyCaseStore`
    instance (never the one that wrote the profile) still finds it,
    scoped to the right firm — the same guarantee `cases`/`drafting_
    documents`/`research_history_entries` already have."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    case_a = _create_case(firm_a, "Dossier A")
    _create_profile(firm_a, case_a, "Dossier A")

    with SessionLocal():
        fresh_store = get_case_store(firm_a.user.firm_id)
        reloaded = fresh_store.get(case_a)
        assert reloaded is not None
        assert reloaded.case_id == case_a

        other_firm_store = get_case_store(uuid.uuid4())
        assert other_firm_store.get(case_a) is None


def _case_get_paths_with_case_id(app_under_test: FastAPI, case_id: str) -> list[str]:
    prefix = "/api/v1/cases/{case_id}"
    paths = [
        route.path.replace("{case_id}", case_id)
        for route in app_under_test.routes
        if getattr(route, "path", "").startswith(prefix)
        and "{case_id}" in getattr(route, "path", "")
        and "GET" in (getattr(route, "methods", None) or set())
    ]
    # `/search` has a required `q` query param — append one so a missing
    # param (422) can't be mistaken for the isolation check (404) this
    # walk is actually testing.
    return [f"{path}?q=test" if path.endswith("/search") else path for path in paths]


def test_no_case_intelligence_get_route_leaks_across_firms(
    authenticated_session: Callable[..., Any], app_under_test: FastAPI
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier A")
    _create_profile(firm_a, case_a, "Dossier A")

    paths = _case_get_paths_with_case_id(app_under_test, case_a)
    assert paths, "le walk de routes ne doit pas être vide"
    for path in paths:
        assert firm_b.client.get(path).status_code == 404, f"{path} fuit cross-firm"


def test_analysis_route_is_isolated_end_to_end(
    authenticated_session: Callable[..., Any],
) -> None:
    """Non-régression composition (docs/19-case-intelligence.md): the
    `/analysis` route (`agents.bootstrap.get_orchestrator`, also
    firm-scoped since ADR-CASEINT-01) must see the exact same profile
    the rest of the resource just wrote, and only for the firm that
    owns it."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    case_a = _create_case(firm_a, "Dossier A")
    _create_profile(firm_a, case_a, "Dossier A")

    ok = firm_a.client.get(f"/api/v1/cases/{case_a}/analysis")
    assert ok.status_code == 200

    leaked = firm_b.client.get(f"/api/v1/cases/{case_a}/analysis")
    assert leaked.status_code == 404
