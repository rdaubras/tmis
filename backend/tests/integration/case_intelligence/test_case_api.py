import asyncio
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
    `TMIS_DATABASE_URL` Postgres. `case_id` is now the id of a real
    `cases` row (ADR-CASEINT-02), so `firms`/`users`/`cases` need to
    exist too, not just `document_records`/`case_profiles`.
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
            core_db_base.Base.metadata.tables["firms"],
            core_db_base.Base.metadata.tables["users"],
            core_db_base.Base.metadata.tables["cases"],
        ],
    )
    core_db_session.SessionLocal.configure(bind=sync_engine)

    clear_case_intelligence_caches()
    get_document_pipeline.cache_clear()
    get_document_store.cache_clear()
    get_kernel.cache_clear()

    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_case(client: TestClient, title: str = "Dossier") -> tuple[str, str]:
    """Every case_intelligence route now requires `case_id` to name a
    real `cases` row the caller's own firm owns (ADR-CASEINT-02) — this
    helper creates one through the real `cases` API (mirrors
    `tests/integration/legal_research/test_research_api_integration.py`
    `_create_case`) and returns `(case_id, firm_id)`."""
    response = client.post("/api/v1/cases", json={"title": title})
    assert response.status_code == 201, response.text
    body = response.json()
    return str(body["id"]), str(body["firm_id"])


def test_create_profile_returns_201(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    response = client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})
    assert response.status_code == 201
    body = response.json()
    assert body["case_id"] == case_id
    assert body["title"] == "Dupont c. ACME"
    assert body["document_ids"] == []


def test_get_profile_returns_404_when_not_created(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    response = client.get(f"/api/v1/cases/{case_id}/profile")
    assert response.status_code == 404


def test_get_profile_returns_404_for_a_case_id_owned_by_no_one(client: TestClient) -> None:
    response = client.get("/api/v1/cases/00000000-0000-0000-0000-000000000000/profile")
    assert response.status_code == 404


def test_get_profile_returns_404_for_a_malformed_case_id(client: TestClient) -> None:
    response = client.get("/api/v1/cases/not-a-uuid/profile")
    assert response.status_code == 404


def test_get_profile_reflects_documents_processed_for_the_case(client: TestClient) -> None:
    case_id, firm_id = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})
    pipeline = get_document_pipeline()
    asyncio.run(
        pipeline.process(
            "bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id=case_id, firm_id=firm_id
        )
    )

    response = client.get(f"/api/v1/cases/{case_id}/profile")

    assert response.status_code == 200
    body = response.json()
    assert len(body["document_ids"]) == 1
    assert len(body["actors"]) == 2
    assert len(body["facts"]) == 1


def test_update_profile_changes_title(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Old title"})
    response = client.patch(f"/api/v1/cases/{case_id}/profile", json={"title": "New title"})
    assert response.status_code == 200
    assert response.json()["title"] == "New title"


def test_update_profile_returns_404_when_not_created(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    response = client.patch(f"/api/v1/cases/{case_id}/profile", json={"title": "X"})
    assert response.status_code == 404


def test_soft_delete_sets_is_deleted_flag(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})
    delete_response = client.delete(f"/api/v1/cases/{case_id}/profile")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/cases/{case_id}/profile")
    assert get_response.json()["is_deleted"] is True


def test_timeline_endpoint_returns_consolidated_entries(client: TestClient) -> None:
    case_id, firm_id = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})
    pipeline = get_document_pipeline()
    asyncio.run(
        pipeline.process(
            "bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id=case_id, firm_id=firm_id
        )
    )

    response = client.get(f"/api/v1/cases/{case_id}/timeline")

    assert response.status_code == 200
    entries = response.json()
    assert len(entries) == 1
    assert entries[0]["date"] == "12 janvier 2019"


def test_timeline_endpoint_returns_404_for_unknown_case(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    assert client.get(f"/api/v1/cases/{case_id}/timeline").status_code == 404


def test_summary_endpoint_returns_all_four_sections(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})
    response = client.get(f"/api/v1/cases/{case_id}/summary")
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
    case_id, firm_id = _create_case(client)
    client.post(f"/api/v1/cases/{case_id}/profile", json={"title": "Dupont c. ACME"})
    pipeline = get_document_pipeline()
    asyncio.run(
        pipeline.process(
            "bail.txt", "text/plain", _CONTRACT_TEXT.encode(), case_id=case_id, firm_id=firm_id
        )
    )

    response = client.get(f"/api/v1/cases/{case_id}/search", params={"q": "bail commercial"})

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_search_endpoint_returns_404_for_unknown_case(client: TestClient) -> None:
    case_id, _ = _create_case(client)
    response = client.get(f"/api/v1/cases/{case_id}/search", params={"q": "test"})
    assert response.status_code == 404


def test_openapi_schema_documents_case_intelligence_routes(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/cases/{case_id}/profile" in paths
    assert "/api/v1/cases/{case_id}/summary" in paths
    assert "/api/v1/cases/{case_id}/timeline" in paths
    assert "/api/v1/cases/{case_id}/search" in paths
