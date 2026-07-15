"""Integration tests for Sprint 39: `GET /api/v1/documents/{document_id}/analysis`,
exposing the real `ContractAgent` (Sprint 35) as a fourth route on the Sprint 26
document resource — see docs/166-architecture-exposition-agent-contrats.md.

Reuses the same real (file-based) sqlite backend fixture as
`test_document_upload_api.py` so uploaded documents flow through the same
`SQLAlchemyDocumentStore` singleton the route reads from, and
`process_document_task` is run directly (not via `.delay()`) to reach the one
status the pipeline actually produces on success: `PROCESSED`.
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
from tmis.agents.bootstrap import get_contract_agent
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.core.db import base as core_db_base
from tmis.core.db import session as core_db_session
from tmis.core.tasks.celery_app import celery_app
from tmis.core.tasks.document_tasks import process_document_task
from tmis.document_intelligence.bootstrap import get_document_pipeline, get_document_store
from tmis.main import app

_CONTRACT_TEXT = (
    "CONTRAT DE PRESTATION DE SERVICES\n\n"
    "Clause de limitation de responsabilité : la responsabilite du "
    "prestataire est totalement exclue en toute circonstance.\n\n"
    "Signé le 12 janvier 2019 par Maître Jean Dupont et la société ACME SARL."
)

_CONTRACT_TEXT_V2 = (
    "CONTRAT DE PRESTATION DE SERVICES\n\n"
    "Clause de limitation de responsabilité : la responsabilite du "
    "prestataire est totalement exclue en toute circonstance.\n\n"
    "Article additionnel : clause de confidentialite ajoutee.\n\n"
    "Signé le 12 janvier 2019 par Maître Jean Dupont et la société ACME SARL."
)


class _FakeAsyncResult:
    def __init__(self, task_id: str) -> None:
        self.id = task_id


@pytest.fixture(autouse=True)
def _sqlite_backend(tmp_path: object, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    db_path = f"{tmp_path}/sprint39.db"  # a file, not :memory:, so sync + async engines share it
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
    get_document_store.cache_clear()
    get_contract_agent.cache_clear()
    from tmis.ai.kernel.bootstrap import get_kernel

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


def test_analysis_returns_404_for_unknown_document(client: TestClient) -> None:
    response = client.get("/api/v1/documents/does-not-exist/analysis")

    assert response.status_code == 404


def test_analysis_returns_409_before_processing_completes(client: TestClient) -> None:
    upload = client.post(
        "/api/v1/documents/upload",
        data={},
        files={"file": ("bail.txt", _CONTRACT_TEXT.encode(), "text/plain")},
    )
    document_id = upload.json()["document_id"]

    response = client.get(f"/api/v1/documents/{document_id}/analysis")

    assert response.status_code == 409
    assert "received" in response.json()["detail"].lower()


def test_analysis_of_a_processed_document(client: TestClient) -> None:
    document_id = _upload_and_process(client, _CONTRACT_TEXT)

    response = client.get(f"/api/v1/documents/{document_id}/analysis")

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert isinstance(body["result"]["clauses"], list)
    assert body["result"]["version_diff"] is None
    assert body["result"]["synthesis"]
    assert body["confidence"] in ("low", "medium", "high")
    assert body["citations"][0]["source_id"] == document_id
    assert isinstance(body["warnings"], list)


def test_analysis_accepts_a_domain_query_param(client: TestClient) -> None:
    document_id = _upload_and_process(client, _CONTRACT_TEXT)

    response = client.get(
        f"/api/v1/documents/{document_id}/analysis", params={"domain": "commercial"}
    )

    assert response.status_code == 200


def test_analysis_rejects_an_unknown_domain(client: TestClient) -> None:
    document_id = _upload_and_process(client, _CONTRACT_TEXT)

    response = client.get(
        f"/api/v1/documents/{document_id}/analysis", params={"domain": "not-a-domain"}
    )

    assert response.status_code == 422


def test_analysis_with_a_valid_compare_document_id(client: TestClient) -> None:
    document_id = _upload_and_process(client, _CONTRACT_TEXT, filename="v1.txt")
    compare_id = _upload_and_process(client, _CONTRACT_TEXT_V2, filename="v2.txt")

    response = client.get(
        f"/api/v1/documents/{document_id}/analysis",
        params={"compare_document_id": compare_id},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["version_diff"] is not None
    assert any(
        "confidentialite" in p.lower()
        for p in body["result"]["version_diff"]["added_paragraphs"]
    )
    assert len(body["citations"]) == 2


def test_analysis_with_an_invalid_compare_document_id_reports_a_warning(
    client: TestClient,
) -> None:
    document_id = _upload_and_process(client, _CONTRACT_TEXT)

    response = client.get(
        f"/api/v1/documents/{document_id}/analysis",
        params={"compare_document_id": "does-not-exist"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["version_diff"] is None
    assert any("does-not-exist" in warning for warning in body["warnings"])


def test_analysis_with_a_known_case_id(client: TestClient) -> None:
    import uuid

    document_id = _upload_and_process(client, _CONTRACT_TEXT)
    case_id = str(uuid.uuid4())
    get_case_intelligence_workflow().case_store.get_or_create(case_id, title="Dossier ACME")

    response = client.get(
        f"/api/v1/documents/{document_id}/analysis", params={"case_id": case_id}
    )

    assert response.status_code == 200
    assert not any("was not found in the case store" in w for w in response.json()["warnings"])


def test_analysis_without_case_id(client: TestClient) -> None:
    document_id = _upload_and_process(client, _CONTRACT_TEXT)

    response = client.get(f"/api/v1/documents/{document_id}/analysis")

    assert response.status_code == 200


def test_upload_route_is_unaffected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/documents/upload",
        data={},
        files={"file": ("bail.txt", _CONTRACT_TEXT.encode(), "text/plain")},
    )

    assert response.status_code == 202
    body: dict[str, Any] = response.json()
    assert body["status"] == "received"


def test_get_document_route_is_unaffected(client: TestClient) -> None:
    document_id = _upload_and_process(client, _CONTRACT_TEXT)

    response = client.get(f"/api/v1/documents/{document_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "processed"


def test_versions_route_is_unaffected(client: TestClient) -> None:
    document_id = _upload_and_process(client, _CONTRACT_TEXT)

    response = client.get(f"/api/v1/documents/{document_id}/versions")

    assert response.status_code == 200
    versions = response.json()
    assert [v["version"] for v in versions] == [1, 2]
