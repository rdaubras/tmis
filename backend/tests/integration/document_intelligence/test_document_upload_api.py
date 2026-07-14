"""End-to-end integration test for Sprint 26 Phase 4: upload API ->
`SQLAlchemyDocumentStore` -> Celery -> `DocumentIntelligencePipeline` ->
next version persisted -> `CaseIntelligenceWorkflow` triggered when a
`case_id` is given -> version-history endpoint (async engine read).

Runs against a real (file-based, so both the sync and async engines see
the same data) sqlite database — not mocks for the DB layer.

`process_document_task.delay()` is stubbed for the API-level tests only:
the FastAPI endpoint runs inside an already-running asyncio event loop
(TestClient drives the async endpoint through one), and Celery's eager
mode executes a task inline in the caller's stack — `asyncio.run()`
inside `process_document_task` would then collide with that outer loop.
In real deployment `.delay()` hands off to a separate Celery worker
process with no event loop of its own, so this collision cannot happen
there; it is purely an artifact of testing an async endpoint synchronously
in-process. The task functions themselves are exercised directly (as
plain function calls, exactly how a Celery worker invokes them) in the
tests below that don't go through the API.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

# Import every domain's SQLAlchemy adapter module so their models are
# registered on `Base.metadata` before `create_all` runs.
import tmis.cabinet_knowledge.knowledge.adapters.sqlalchemy_store  # noqa: F401
import tmis.case_intelligence.cases.adapters.sqlalchemy_store  # noqa: F401
import tmis.collaboration.workspace.adapters.sqlalchemy_store  # noqa: F401
import tmis.document_intelligence.adapters.sqlalchemy_store  # noqa: F401
import tmis.legal_drafting.documents.sqlalchemy_store  # noqa: F401
import tmis.legal_reasoning.reasoner.sqlalchemy_store  # noqa: F401
import tmis.legal_research.history.adapters.sqlalchemy_store  # noqa: F401
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.case_intelligence.cases.adapters.sqlalchemy_store import SQLAlchemyCaseStore
from tmis.core.db import base as core_db_base
from tmis.core.db import session as core_db_session
from tmis.core.tasks.celery_app import celery_app
from tmis.core.tasks.document_tasks import process_document_task
from tmis.document_intelligence.bootstrap import get_document_pipeline
from tmis.main import app

_CONTRACT_TEXT = (
    "CONTRAT DE BAIL COMMERCIAL\n\n"
    "Signé le 12 janvier 2019 par Maître Jean Dupont et la société ACME SARL."
)


class _FakeAsyncResult:
    def __init__(self, task_id: str) -> None:
        self.id = task_id


@pytest.fixture(autouse=True)
def _sqlite_backend(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    db_path = f"{tmp_path}/sprint26.db"  # a file, not :memory:, so sync + async engines share it
    sync_engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    core_db_base.Base.metadata.create_all(sync_engine)
    core_db_session.SessionLocal.configure(bind=sync_engine)

    async_engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_db_session.AsyncSessionLocal.configure(bind=async_engine)

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    monkeypatch.setattr(
        process_document_task, "delay", lambda *a, **kw: _FakeAsyncResult("fake-task-id")
    )

    get_case_intelligence_workflow.cache_clear()
    get_document_pipeline.cache_clear()
    from tmis.ai.kernel.bootstrap import get_kernel

    get_kernel.cache_clear()

    yield

    celery_app.conf.task_always_eager = False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _upload(client: TestClient, *, case_id: str | None = None) -> dict[str, Any]:
    data = {"case_id": case_id} if case_id else {}
    response = client.post(
        "/api/v1/documents/upload",
        data=data,
        files={"file": ("bail.txt", _CONTRACT_TEXT.encode(), "text/plain")},
    )
    assert response.status_code == 202
    result: dict[str, Any] = response.json()
    return result


def test_upload_persists_initial_record_and_returns_202(client: TestClient) -> None:
    body = _upload(client)

    assert body["status"] == "received"
    assert body["document_id"]
    assert body["task_id"] == "fake-task-id"

    get_response = client.get(f"/api/v1/documents/{body['document_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["status"] == "received"


def test_get_document_returns_404_for_unknown_id(client: TestClient) -> None:
    assert client.get("/api/v1/documents/does-not-exist").status_code == 404


def test_version_history_returns_404_for_unknown_document(client: TestClient) -> None:
    assert client.get("/api/v1/documents/does-not-exist/versions").status_code == 404


def test_version_history_lists_only_the_initial_version_before_processing(
    client: TestClient,
) -> None:
    body = _upload(client)

    versions = client.get(f"/api/v1/documents/{body['document_id']}/versions").json()

    assert [v["version"] for v in versions] == [1]
    assert versions[0]["status"] == "received"
    assert versions[0]["previous_version_id"] is None


def test_process_document_task_persists_the_next_version(client: TestClient) -> None:
    body = _upload(client)
    document_id = body["document_id"]

    result_id = process_document_task(document_id, "bail.txt", "text/plain", None)

    assert result_id == document_id
    get_response = client.get(f"/api/v1/documents/{document_id}")
    assert get_response.status_code == 200
    processed = get_response.json()
    assert processed["status"] == "processed"
    assert "bail" in processed["ocr_text"].lower()

    versions = client.get(f"/api/v1/documents/{document_id}/versions").json()
    assert [v["version"] for v in versions] == [1, 2]
    assert versions[1]["previous_version_id"] is not None


def test_process_document_task_with_case_id_triggers_case_enrichment(client: TestClient) -> None:
    # Note: the synchronous /api/v1/cases endpoints still read/write via
    # `get_case_intelligence_workflow()`'s default `InMemoryCaseStore`
    # (Sprint 4 wiring, unchanged by this sprint — see
    # docs/151-architecture-persistance.md, "Known seam"), while the
    # Celery-triggered path below uses `SQLAlchemyCaseStore` explicitly.
    # So this test verifies enrichment through the same SQLAlchemy store
    # the task itself uses, not through the in-memory-backed API.
    body = _upload(client, case_id="case-1")
    document_id = body["document_id"]

    process_document_task(document_id, "bail.txt", "text/plain", "case-1")

    profile = SQLAlchemyCaseStore().get("case-1")
    assert profile is not None
    assert len(profile.document_ids) == 1
