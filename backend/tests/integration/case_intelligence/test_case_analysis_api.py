"""Integration tests for Sprint 41: `GET /api/v1/cases/{case_id}/analysis`,
exposing the fully wired `Orchestrator` (`agents.bootstrap.
get_orchestrator()`) as a sixth route on the Sprint 19 case_intelligence
resource — see docs/168-architecture-exposition-orchestrator.md.

Reuses the same real (file-based) sqlite backend fixture as
`test_document_analysis_api.py` so `AnalysisAgent` reads uploaded documents
through the same shared `SQLAlchemyDocumentStore` singleton the orchestrator
now uses (Sprint 41 Part A), and `process_document_task` is run directly
(not via `.delay()`) to reach `PROCESSED`, the one status the pipeline
actually produces on success.

`case_id` in this router is a free-form string (`CaseStorePort.get`), while
`AgentInput.case_id` is typed `uuid.UUID | None` — a UUID-formatted case id
is used below wherever the test needs `SynthesisAgent` to actually resolve
the `CaseProfile` (see `_parse_case_id_for_agent` in `routes.py`); a
non-UUID case id (`"case-1"`, like the rest of this module's tests) is used
to exercise the documented fallback instead.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import tmis.document_intelligence.adapters.sqlalchemy_store  # noqa: F401
from tmis.agents.bootstrap import get_orchestrator
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.core.db import base as core_db_base
from tmis.core.db import session as core_db_session
from tmis.core.tasks.celery_app import celery_app
from tmis.core.tasks.document_tasks import process_document_task
from tmis.document_intelligence.bootstrap import get_document_pipeline, get_document_store
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
    sync_engine = create_engine(
        f"sqlite:///{tmp_path}/sprint41-case-analysis.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_db_base.Base.metadata.create_all(
        sync_engine, tables=[core_db_base.Base.metadata.tables["document_records"]]
    )
    core_db_session.SessionLocal.configure(bind=sync_engine)

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    monkeypatch.setattr(
        process_document_task, "delay", lambda *a, **kw: _FakeAsyncResult("fake-task-id")
    )

    get_case_intelligence_workflow.cache_clear()
    get_document_pipeline.cache_clear()
    get_document_store.cache_clear()
    get_orchestrator.cache_clear()
    get_kernel.cache_clear()

    yield

    celery_app.conf.task_always_eager = False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _upload_and_process(client: TestClient, text: str, filename: str = "bail.txt") -> str:
    response = client.post(
        "/api/v1/documents/upload",
        data={},
        files={"file": (filename, text.encode(), "text/plain")},
    )
    assert response.status_code == 202
    document_id: str = response.json()["document_id"]
    process_document_task(document_id, filename, "text/plain", None)
    return document_id


def test_analysis_returns_404_for_unknown_case(client: TestClient) -> None:
    response = client.get("/api/v1/cases/does-not-exist/analysis")

    assert response.status_code == 404


def test_analysis_without_document_id_for_an_existing_case(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})

    response = client.get("/api/v1/cases/case-1/analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == "case-1"
    assert body["result"]["entities"] == {}
    assert "synthesis" in body["result"]
    assert any("document_id" in warning for warning in body["warnings"])


def test_analysis_with_a_document_id(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})
    document_id = _upload_and_process(client, _CONTRACT_TEXT)

    response = client.get(
        "/api/v1/cases/case-1/analysis", params={"document_id": document_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert any(len(v) > 0 for v in body["result"]["entities"].values())
    assert body["result"]["narrative"]
    assert body["result"]["model"]
    assert "synthesis" in body["result"]
    assert any(c["source_id"] == document_id for c in body["citations"])


def test_analysis_with_an_unknown_document_id_reports_a_warning(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})

    response = client.get(
        "/api/v1/cases/case-1/analysis", params={"document_id": "does-not-exist"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["entities"] == {}
    assert any("does-not-exist" in warning for warning in body["warnings"])


def test_analysis_with_a_uuid_case_id_populates_the_synthesis(client: TestClient) -> None:
    import uuid

    case_id = str(uuid.uuid4())
    get_case_intelligence_workflow().case_store.get_or_create(case_id, title="Dossier ACME")
    document_id = _upload_and_process(client, _CONTRACT_TEXT)

    response = client.get(
        f"/api/v1/cases/{case_id}/analysis", params={"document_id": document_id}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["synthesis"]["executive_summary"]
    assert any(c["connector"] == "case_store" for c in body["citations"])


def test_analysis_with_a_non_uuid_case_id_still_succeeds(client: TestClient) -> None:
    """`case_id` in this router is free-form (`"case-1"`), but `AgentInput.
    case_id` is `uuid.UUID | None`: a non-UUID case id parses to `None`
    (see `_parse_case_id_for_agent`), so `SynthesisAgent` reports it as
    missing via a warning rather than failing the request — the same
    graceful degradation `AnalysisAgent` already applies to a missing
    `document_id`."""
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})

    response = client.get("/api/v1/cases/case-1/analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["synthesis"]["executive_summary"] == ""
    assert any("No case_id provided" in warning for warning in body["warnings"])


def test_profile_route_is_unaffected(client: TestClient) -> None:
    response = client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})

    assert response.status_code == 201
    assert response.json()["case_id"] == "case-1"


def test_summary_route_is_unaffected(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})

    response = client.get("/api/v1/cases/case-1/summary")

    assert response.status_code == 200
    assert set(response.json()) == {
        "executive_summary",
        "chronological_summary",
        "documentary_summary",
        "case_status",
        "open_points",
    }


def test_openapi_schema_documents_the_analysis_route(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/cases/{case_id}/analysis" in response.json()["paths"]
