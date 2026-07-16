import asyncio
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import tmis.case_intelligence.cases.adapters.sqlalchemy_store  # noqa: F401
import tmis.document_intelligence.adapters.sqlalchemy_store  # noqa: F401
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow, get_case_store
from tmis.core.db import base as core_db_base
from tmis.core.db import session as core_db_session
from tmis.document_intelligence.bootstrap import get_document_pipeline, get_document_store
from tmis.main import app

_CONTRACT_TEXT = (
    "CONTRAT DE BAIL COMMERCIAL\n\n"
    "Signé le 12 janvier 2019 par Maître Jean Dupont et la société ACME SARL."
)


@pytest.fixture(autouse=True)
def _clear_singletons(tmp_path: object) -> Iterator[None]:
    """The bootstrap accessors are `lru_cache`d process-wide singletons;
    reset them before each test so cases created by one test don't leak
    into another (see docs/19-case-intelligence.md).

    `get_document_pipeline()` now saves through the shared
    `SQLAlchemyDocumentStore` singleton (Sprint 37) instead of an
    in-memory default, so this test points the module-wide sync
    `SessionLocal` at a throwaway sqlite database — same real-DB fixture
    pattern as `test_document_upload_api.py` — rather than the real
    `TMIS_DATABASE_URL` Postgres.
    """
    sync_engine = create_engine(
        f"sqlite:///{tmp_path}/sprint37-case-api.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_db_base.Base.metadata.create_all(
        sync_engine,
        tables=[
            core_db_base.Base.metadata.tables["document_records"],
            core_db_base.Base.metadata.tables["case_profiles"],
        ],
    )
    core_db_session.SessionLocal.configure(bind=sync_engine)

    get_case_intelligence_workflow.cache_clear()
    get_case_store.cache_clear()
    get_document_pipeline.cache_clear()
    get_document_store.cache_clear()
    from tmis.ai.kernel.bootstrap import get_kernel

    get_kernel.cache_clear()

    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_profile_returns_201(client: TestClient) -> None:
    response = client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})
    assert response.status_code == 201
    body = response.json()
    assert body["case_id"] == "case-1"
    assert body["title"] == "Dupont c. ACME"
    assert body["document_ids"] == []


def test_get_profile_returns_404_when_not_created(client: TestClient) -> None:
    response = client.get("/api/v1/cases/does-not-exist/profile")
    assert response.status_code == 404


def test_get_profile_reflects_documents_processed_for_the_case(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})
    pipeline = get_document_pipeline()
    asyncio.run(
        pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id="case-1")
    )

    response = client.get("/api/v1/cases/case-1/profile")

    assert response.status_code == 200
    body = response.json()
    assert len(body["document_ids"]) == 1
    assert len(body["actors"]) == 2
    assert len(body["facts"]) == 1


def test_update_profile_changes_title(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Old title"})
    response = client.patch("/api/v1/cases/case-1/profile", json={"title": "New title"})
    assert response.status_code == 200
    assert response.json()["title"] == "New title"


def test_update_profile_returns_404_when_not_created(client: TestClient) -> None:
    response = client.patch("/api/v1/cases/does-not-exist/profile", json={"title": "X"})
    assert response.status_code == 404


def test_soft_delete_sets_is_deleted_flag(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})
    delete_response = client.delete("/api/v1/cases/case-1/profile")
    assert delete_response.status_code == 204

    get_response = client.get("/api/v1/cases/case-1/profile")
    assert get_response.json()["is_deleted"] is True


def test_timeline_endpoint_returns_consolidated_entries(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})
    pipeline = get_document_pipeline()
    asyncio.run(
        pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id="case-1")
    )

    response = client.get("/api/v1/cases/case-1/timeline")

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["date"] == "12 janvier 2019"


def test_timeline_endpoint_returns_404_for_unknown_case(client: TestClient) -> None:
    assert client.get("/api/v1/cases/does-not-exist/timeline").status_code == 404


def test_summary_endpoint_returns_all_four_sections(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})
    response = client.get("/api/v1/cases/case-1/summary")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "executive_summary",
        "chronological_summary",
        "documentary_summary",
        "case_status",
        "open_points",
    }


def test_search_endpoint_finds_indexed_facts(client: TestClient) -> None:
    client.post("/api/v1/cases/case-1/profile", json={"title": "Dupont c. ACME"})
    pipeline = get_document_pipeline()
    asyncio.run(
        pipeline.process("bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id="case-1")
    )

    response = client.get("/api/v1/cases/case-1/search", params={"q": "bail commercial"})

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_search_endpoint_returns_404_for_unknown_case(client: TestClient) -> None:
    response = client.get("/api/v1/cases/does-not-exist/search", params={"q": "test"})
    assert response.status_code == 404


def test_openapi_schema_documents_case_intelligence_routes(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/cases/{case_id}/profile" in paths
    assert "/api/v1/cases/{case_id}/summary" in paths
    assert "/api/v1/cases/{case_id}/timeline" in paths
    assert "/api/v1/cases/{case_id}/search" in paths
