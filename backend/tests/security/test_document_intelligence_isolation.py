"""Isolation tests for the "document_intelligence" persistent & isolated
slice — the last conversion of Axe A (ADR-DOCINT-01, see
docs/14-document-intelligence.md). Talks to the real app through
`authenticated_session` (real, signed JWTs via `/auth/login`) — nothing
here bypasses the auth boundary, matching every other test in this
directory (see `tests/security/test_case_intelligence_isolation.py`,
which this one mirrors).

`document_records` carries `raw_bytes` — the uploaded file itself, not
derived metadata — so the central test in this file
(`test_firm_b_cannot_read_firm_as_raw_bytes`) asserts on the store
directly, not only on the HTTP response (`DocumentSummaryResponse` never
serializes `raw_bytes` in the first place, so a passing HTTP-only test
would not by itself prove the byte content is unreachable): a
cross-firm `get()` must return `None`, not a record whose `raw_bytes`
happens to be withheld by the response schema.

`process_document_task` is invoked directly (not through `.delay()`) for
the write-path tests below — as a Celery worker would call it — mirroring
`test_case_intelligence_isolation.py`'s own task-tests.
"""

import uuid
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

import tmis.document_intelligence.adapters.sqlalchemy_store  # noqa: F401 — registers document_records
from tmis.core.database import Base as sync_base
from tmis.core.db import session as core_db_session
from tmis.core.tasks.celery_app import celery_app
from tmis.core.tasks.document_tasks import process_document_task
from tmis.document_intelligence.adapters.sqlalchemy_store import SQLAlchemyDocumentStore
from tmis.document_intelligence.bootstrap import get_document_knowledge_graph, get_document_store
from tmis.document_intelligence.schemas.document import ProcessingStatus
from tmis.document_intelligence.schemas.record import DocumentRecord

_CONTRACT_TEXT = (
    "CONTRAT DE BAIL COMMERCIAL CONFIDENTIEL\n\n"
    "Signé le 12 janvier 2019 par Maître Jean Dupont et la société ACME SARL."
)


class _FakeAsyncResult:
    def __init__(self, task_id: str) -> None:
        self.id = task_id


@pytest.fixture(autouse=True)
def _wire_async_engine_and_clear_caches(
    tmp_path: object, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    """`tests/security/conftest.py`'s own autouse `_sqlite_database`
    fixture already points the *sync* engine (`tmis.core.database.
    SessionLocal`, what `SQLAlchemyDocumentStore` uses) at a per-test
    sqlite file — `{tmp_path}/security.db`. `GET /{document_id}/versions`
    reads through the *async* engine instead (see
    `tmis.api.v1.document.routes`'s own module docstring for why), so
    this fixture points `AsyncSessionLocal` at that exact same file —
    same pattern as `tests/integration/document_intelligence/
    test_document_upload_api.py`.
    """
    sync_engine = create_engine(
        f"sqlite:///{tmp_path}/security.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    sync_base.metadata.create_all(sync_engine)
    core_db_session.SessionLocal.configure(bind=sync_engine)

    async_engine = create_async_engine(
        f"sqlite+aiosqlite:///{tmp_path}/security.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_db_session.AsyncSessionLocal.configure(bind=async_engine)

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    monkeypatch.setattr(
        process_document_task, "delay", lambda *a, **kw: _FakeAsyncResult("fake-task-id")
    )

    get_document_knowledge_graph.cache_clear()

    yield

    celery_app.conf.task_always_eager = False


def _seed_processed_document(firm_id: uuid.UUID | str, document_id: str | None = None) -> str:
    """Persists a `PROCESSED` `DocumentRecord` directly through the real
    `SQLAlchemyDocumentStore`, scoped to `firm_id` — bypassing the
    upload API/Celery task, since most tests below only need a document
    to exist for the right firm, not a full pipeline run."""
    document_id = document_id or str(uuid.uuid4())
    SQLAlchemyDocumentStore(firm_id=firm_id).save(
        DocumentRecord(
            document_id=document_id,
            filename="bail-confidentiel.txt",
            status=ProcessingStatus.PROCESSED,
            raw_bytes=_CONTRACT_TEXT.encode(),
            ocr_text=_CONTRACT_TEXT,
        )
    )
    return document_id


def _upload(session: Any, *, case_id: str | None = None) -> dict[str, Any]:
    data = {"case_id": case_id} if case_id else {}
    response = session.client.post(
        "/api/v1/documents/upload",
        data=data,
        files={"file": ("bail.txt", _CONTRACT_TEXT.encode(), "text/plain")},
    )
    assert response.status_code == 202, response.text
    result: dict[str, Any] = response.json()
    return result


def test_firm_b_cannot_read_firm_as_raw_bytes(
    authenticated_session: Callable[..., Any],
) -> None:
    """The central test of this sprint (§7 of docs/14-document-
    intelligence.md, "raw_bytes est la donnée la plus sensible du
    produit"): a document belonging to firm A must be completely
    unreachable — including its raw bytes — from firm B, at the store
    level, not only through whatever fields the HTTP response happens to
    serialize."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    document_id = _seed_processed_document(firm_a.user.firm_id)

    assert get_document_store(firm_b.user.firm_id).get(document_id) is None
    assert get_document_store(firm_b.user.firm_id).list_versions(document_id) == []

    own = get_document_store(firm_a.user.firm_id).get(document_id)
    assert own is not None
    assert own.raw_bytes == _CONTRACT_TEXT.encode()


def test_firm_b_gets_404_reading_firm_as_document(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    document_id = _seed_processed_document(firm_a.user.firm_id)

    response = firm_b.client.get(f"/api/v1/documents/{document_id}")
    assert response.status_code == 404
    assert "confidentiel" not in response.text.lower()

    ok = firm_a.client.get(f"/api/v1/documents/{document_id}")
    assert ok.status_code == 200


def test_firm_b_gets_404_reading_firm_as_versions(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    document_id = _seed_processed_document(firm_a.user.firm_id)

    response = firm_b.client.get(f"/api/v1/documents/{document_id}/versions")
    assert response.status_code == 404

    ok = firm_a.client.get(f"/api/v1/documents/{document_id}/versions")
    assert ok.status_code == 200


def test_isolation_is_symmetric(authenticated_session: Callable[..., Any]) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    document_a = _seed_processed_document(firm_a.user.firm_id)
    document_b = _seed_processed_document(firm_b.user.firm_id)

    assert firm_a.client.get(f"/api/v1/documents/{document_b}").status_code == 404
    assert firm_b.client.get(f"/api/v1/documents/{document_a}").status_code == 404
    assert firm_a.client.get(f"/api/v1/documents/{document_b}/versions").status_code == 404
    assert firm_b.client.get(f"/api/v1/documents/{document_a}/versions").status_code == 404


def test_analyze_document_returns_404_for_a_document_owned_by_another_firm(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    document_id = _seed_processed_document(firm_a.user.firm_id)

    response = firm_b.client.get(f"/api/v1/documents/{document_id}/analysis")
    assert response.status_code == 404

    ok = firm_a.client.get(f"/api/v1/documents/{document_id}/analysis")
    assert ok.status_code == 200


def test_process_document_task_stamps_the_document_with_its_own_firm_id(
    authenticated_session: Callable[..., Any],
) -> None:
    """T4 (docs/14-document-intelligence.md): the Celery task is invoked
    directly (as a worker would call it) with firm B's `firm_id` — the
    resulting document must be readable by firm B and invisible to firm
    A, proving `firm_id` is used to build the scoped store, not just
    relayed to case_intelligence."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    upload = _upload(firm_b)
    document_id = upload["document_id"]

    process_document_task(document_id, "bail.txt", "text/plain", None, str(firm_b.user.firm_id))

    processed = get_document_store(firm_b.user.firm_id).get(document_id)
    assert processed is not None
    assert processed.status is ProcessingStatus.PROCESSED

    assert get_document_store(firm_a.user.firm_id).get(document_id) is None
    assert firm_a.client.get(f"/api/v1/documents/{document_id}").status_code == 404


def test_process_document_task_without_firm_id_raises(
    authenticated_session: Callable[..., Any],
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    upload = _upload(firm_a)

    with pytest.raises(ValueError, match="requires firm_id"):
        process_document_task(upload["document_id"], "bail.txt", "text/plain", None, None)


def test_upload_without_case_id_is_stamped_to_the_uploaders_firm(
    authenticated_session: Callable[..., Any],
) -> None:
    """ADR-DOCINT-01 (docs/14-document-intelligence.md): a document
    uploaded with no `case_id` at all must still be estampillé to the
    uploader's own firm (from the token, never derived from `case_id`)
    and readable only by that firm."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    upload = _upload(firm_a)
    document_id = upload["document_id"]

    stored = get_document_store(firm_a.user.firm_id).get(document_id)
    assert stored is not None

    assert get_document_store(firm_b.user.firm_id).get(document_id) is None
    assert firm_a.client.get(f"/api/v1/documents/{document_id}").status_code == 200
    assert firm_b.client.get(f"/api/v1/documents/{document_id}").status_code == 404


def test_document_knowledge_graph_is_partitioned_per_firm(
    authenticated_session: Callable[..., Any],
) -> None:
    """T5 (docs/14-document-intelligence.md): the knowledge graph a
    firm's documents populate must never be visible from another firm's
    partition — `get_document_knowledge_graph` is the accessor every
    write/read path goes through, so this asserts on it directly (there
    is no dedicated HTTP route exposing the raw graph)."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    upload = _upload(firm_a)
    document_id = upload["document_id"]
    process_document_task(document_id, "bail.txt", "text/plain", None, str(firm_a.user.firm_id))

    graph_a = get_document_knowledge_graph(firm_a.user.firm_id)
    graph_b = get_document_knowledge_graph(firm_b.user.firm_id)

    # `KnowledgeGraphBuilder.update()` (`document_intelligence.knowledge.
    # builder`) uses the bare `document_id` as the document node's own id.
    assert graph_a.get_node(document_id) is not None
    assert graph_b.get_node(document_id) is None


def test_document_store_persists_across_a_brand_new_session_and_store_instance(
    authenticated_session: Callable[..., Any],
) -> None:
    """Persistence-survives-restart: a fresh `SQLAlchemyDocumentStore`
    instance (never the one that wrote the record) still finds it,
    scoped to the right firm — the same guarantee `cases`/`case_
    profiles`/`drafting_documents`/`research_history_entries` already
    have."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    document_id = _seed_processed_document(firm_a.user.firm_id)

    with core_db_session.SessionLocal():
        fresh_store = get_document_store(firm_a.user.firm_id)
        reloaded = fresh_store.get(document_id)
        assert reloaded is not None
        assert reloaded.document_id == document_id

        other_firm_store = get_document_store(uuid.uuid4())
        assert other_firm_store.get(document_id) is None


def _document_get_paths_with_document_id(app_under_test: FastAPI, document_id: str) -> list[str]:
    prefix = "/api/v1/documents/{document_id}"
    return [
        route.path.replace("{document_id}", document_id)
        for route in app_under_test.routes
        if getattr(route, "path", "").startswith(prefix)
        and "{document_id}" in getattr(route, "path", "")
        and "GET" in (getattr(route, "methods", None) or set())
    ]


def test_no_document_intelligence_get_route_leaks_across_firms(
    authenticated_session: Callable[..., Any], app_under_test: FastAPI
) -> None:
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    document_id = _seed_processed_document(firm_a.user.firm_id)

    paths = _document_get_paths_with_document_id(app_under_test, document_id)
    assert paths, "le walk de routes ne doit pas être vide"
    for path in paths:
        assert firm_b.client.get(path).status_code == 404, f"{path} fuit cross-firm"


def test_upload_to_analysis_composition_is_isolated_end_to_end(
    authenticated_session: Callable[..., Any],
) -> None:
    """Non-régression composition (docs/14-document-intelligence.md):
    upload -> `process_document_task` -> `GET .../analysis` must stay
    green end-to-end, scoped to the right firm only — closing the loop
    the whole Axe A roadmap builds towards (`document -> case ->
    draft/research`)."""
    firm_a = authenticated_session(email="a@example.com", firm_name="Cabinet A")
    firm_b = authenticated_session(email="b@example.com", firm_name="Cabinet B")

    upload = _upload(firm_a)
    document_id = upload["document_id"]
    process_document_task(document_id, "bail.txt", "text/plain", None, str(firm_a.user.firm_id))

    ok = firm_a.client.get(f"/api/v1/documents/{document_id}/analysis")
    assert ok.status_code == 200
    assert ok.json()["document_id"] == document_id

    leaked = firm_b.client.get(f"/api/v1/documents/{document_id}/analysis")
    assert leaked.status_code == 404
