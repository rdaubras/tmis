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

Since ADR-CASEINT-02 (docs/19-case-intelligence.md, "case_intelligence"
persistent & isolated slice), `case_id` in this router must name a real
`cases` row the caller's own firm owns — no longer a free-form string a
test can invent (`"case-1"`), so every test here goes through `_create_case`
first, mirroring `test_case_api.py`. `get_orchestrator` is also firm-scoped
now (ADR-CASEINT-01) and no longer an `lru_cache` singleton.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import tmis.case_intelligence.cases.adapters.sqlalchemy_store  # noqa: F401
import tmis.document_intelligence.adapters.sqlalchemy_store  # noqa: F401
import tmis.infrastructure.persistence.models  # noqa: F401 — registers firms/users/cases
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import clear_case_intelligence_caches
from tmis.core.db import base as core_db_base
from tmis.core.db import session as core_db_session
from tmis.core.tasks.celery_app import celery_app
from tmis.core.tasks.document_tasks import process_document_task
from tmis.document_intelligence.bootstrap import get_document_knowledge_graph
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
        sync_engine,
        tables=[
            core_db_base.Base.metadata.tables["document_records"],
            core_db_base.Base.metadata.tables["case_profiles"],
            core_db_base.Base.metadata.tables["firms"],
            core_db_base.Base.metadata.tables["users"],
            core_db_base.Base.metadata.tables["cases"],
        ],
    )
    core_db_session.SessionLocal.configure(bind=sync_engine)

    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    monkeypatch.setattr(
        process_document_task, "delay", lambda *a, **kw: _FakeAsyncResult("fake-task-id")
    )

    clear_case_intelligence_caches()
    get_document_knowledge_graph.cache_clear()
    get_kernel.cache_clear()

    yield

    celery_app.conf.task_always_eager = False


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_case(client: TestClient, title: str = "Dossier") -> tuple[str, str]:
    response = client.post("/api/v1/cases", json={"title": title})
    assert response.status_code == 201, response.text
    body = response.json()
    return str(body["id"]), str(body["firm_id"])


def _upload_and_process(
    client: TestClient, text: str, firm_id: str, filename: str = "bail.txt"
) -> str:
    response = client.post(
        "/api/v1/documents/upload",
        data={},
        files={"file": (filename, text.encode(), "text/plain")},
    )
    assert response.status_code == 202
    document_id: str = response.json()["document_id"]
    process_document_task(document_id, filename, "text/plain", None, firm_id)
    return document_id


def test_analysis_returns_404_for_unknown_case(client: TestClient) -> None:
    response = client.get("/api/v1/cases/00000000-0000-0000-0000-000000000000/analysis")

    assert response.status_code == 404


def test_analysis_without_document_id_for_an_existing_case(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})

    response = client.get(f"/api/v1/cases/{case_id}/analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == case_id
    assert body["result"]["entities"] == {}
    assert "synthesis" in body["result"]
    assert any("document_id" in warning for warning in body["warnings"])


def test_analysis_with_a_document_id(client: TestClient) -> None:
    case_id, firm_id = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})
    document_id = _upload_and_process(client, _CONTRACT_TEXT, firm_id)

    response = client.get(f"/api/v1/cases/{case_id}/analysis", params={"document_id": document_id})

    assert response.status_code == 200
    body = response.json()
    assert any(len(v) > 0 for v in body["result"]["entities"].values())
    assert body["result"]["narrative"]
    assert body["result"]["model"]
    assert "synthesis" in body["result"]
    assert any(c["source_id"] == document_id for c in body["citations"])


def test_analysis_with_an_unknown_document_id_reports_a_warning(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})

    response = client.get(
        f"/api/v1/cases/{case_id}/analysis", params={"document_id": "does-not-exist"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["entities"] == {}
    assert any("does-not-exist" in warning for warning in body["warnings"])


def test_analysis_populates_the_synthesis_from_the_case_profile(client: TestClient) -> None:
    case_id, firm_id = _create_case(client, "Dossier ACME")
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dossier ACME"})
    document_id = _upload_and_process(client, _CONTRACT_TEXT, firm_id)

    response = client.get(f"/api/v1/cases/{case_id}/analysis", params={"document_id": document_id})

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["synthesis"]["executive_summary"]
    assert any(c["connector"] == "case_store" for c in body["citations"])


def test_analysis_returns_404_for_a_malformed_case_id(client: TestClient) -> None:
    response = client.get("/api/v1/cases/not-a-uuid/analysis")

    assert response.status_code == 404


def test_profile_route_is_unaffected(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    response = client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})

    assert response.status_code == 201
    assert response.json()["case_id"] == case_id


def test_summary_route_is_unaffected(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})

    response = client.get(f"/api/v1/cases/{case_id}/summary")

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
