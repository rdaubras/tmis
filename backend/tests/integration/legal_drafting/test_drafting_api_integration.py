from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

import tmis.infrastructure.persistence.models  # noqa: F401 — registers firms/users/cases
import tmis.legal_drafting.documents.sqlalchemy_store  # noqa: F401 — registers drafting_documents
import tmis.legal_drafting.versioning.sqlalchemy_service  # noqa: F401 — registers versions table
from tmis.ai.kernel.bootstrap import get_kernel
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
from tmis.core import database as core_database
from tmis.legal_drafting.bootstrap import (
    get_draft_history,
    get_style_engine,
    get_style_registry,
    get_template_registry,
    get_validation_service,
)
from tmis.legal_reasoning.bootstrap import get_reasoning_orchestrator
from tmis.legal_research.bootstrap import get_research_orchestrator
from tmis.main import app

_QUESTION = "contrat de travail à durée indéterminée peut être rompu"


@pytest.fixture(autouse=True)
def _clear_singletons(tmp_path: object) -> Iterator[None]:
    """The document orchestrator itself is no longer an `lru_cache`
    singleton (ADR-SLICE-02, docs/28-legal-drafting.md) — it is now
    assembled per request on the request's own `Session`, scoped to the
    caller's `firm_id`. This fixture points that shared sync engine at a
    throwaway sqlite database (same pattern as
    `tests/security/conftest.py`) instead of whatever `TMIS_DATABASE_URL`
    happens to be configured to, and resets the collaborators that are
    still process-wide singletons."""
    engine = create_engine(
        f"sqlite:///{tmp_path}/drafting-api.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    core_database.SessionLocal.configure(bind=engine)
    core_database.Base.metadata.create_all(engine)

    get_reasoning_orchestrator.cache_clear()
    get_research_orchestrator.cache_clear()
    get_case_intelligence_workflow.cache_clear()
    get_kernel.cache_clear()
    get_template_registry.cache_clear()
    get_style_registry.cache_clear()
    get_style_engine.cache_clear()
    get_draft_history.cache_clear()
    get_validation_service.cache_clear()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _create_draft(client: TestClient, **overrides: object) -> dict:
    payload = {"document_type": "consultation", "question": _QUESTION}
    payload.update(overrides)
    response = client.post("/api/v1/legal-drafting/drafts", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_draft_returns_a_draft_with_sections(client: TestClient) -> None:
    body = _create_draft(client)
    assert body["is_draft"] is True
    assert body["status"] == "under_review"
    assert body["sections"]


def test_get_draft_retrieves_a_previously_created_draft(client: TestClient) -> None:
    created = _create_draft(client)
    response = client.get(f"/api/v1/legal-drafting/drafts/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_draft_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/api/v1/legal-drafting/drafts/does-not-exist")
    assert response.status_code == 404


def test_regenerate_section_keeps_the_section_id(client: TestClient) -> None:
    created = _create_draft(client)
    section = next(s for s in created["sections"] if s["key"] == "context")

    response = client.post(
        f"/api/v1/legal-drafting/drafts/{created['id']}/sections/context/regenerate"
    )

    assert response.status_code == 200
    new_section = next(s for s in response.json()["sections"] if s["key"] == "context")
    assert new_section["id"] == section["id"]


def test_regenerate_section_unknown_returns_404(client: TestClient) -> None:
    created = _create_draft(client)
    response = client.post(
        f"/api/v1/legal-drafting/drafts/{created['id']}/sections/unknown/regenerate"
    )
    assert response.status_code == 404


def test_regenerate_paragraph_keeps_the_paragraph_id(client: TestClient) -> None:
    created = _create_draft(client)
    section = next(s for s in created["sections"] if s["key"] == "context")
    paragraph_id = section["paragraphs"][0]["id"]

    response = client.post(
        f"/api/v1/legal-drafting/drafts/{created['id']}/sections/context/"
        f"paragraphs/{paragraph_id}/regenerate"
    )

    assert response.status_code == 200
    new_section = next(s for s in response.json()["sections"] if s["key"] == "context")
    assert new_section["paragraphs"][0]["id"] == paragraph_id


def test_versions_list_grows_after_regeneration(client: TestClient) -> None:
    created = _create_draft(client)
    client.post(f"/api/v1/legal-drafting/drafts/{created['id']}/sections/context/regenerate")

    response = client.get(f"/api/v1/legal-drafting/drafts/{created['id']}/versions")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_compare_versions_endpoint(client: TestClient) -> None:
    created = _create_draft(client)
    client.post(f"/api/v1/legal-drafting/drafts/{created['id']}/sections/context/regenerate")

    response = client.get(
        f"/api/v1/legal-drafting/drafts/{created['id']}/versions/compare",
        params={"version_a": 1, "version_b": 2},
    )

    assert response.status_code == 200
    assert response.json()["version_a"] == 1


def test_validate_endpoint_records_a_decision(client: TestClient) -> None:
    created = _create_draft(client)
    response = client.post(
        f"/api/v1/legal-drafting/drafts/{created['id']}/validate",
        json={"decision": "approved", "author": "avocat@cabinet.fr"},
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "approved"

    draft = client.get(f"/api/v1/legal-drafting/drafts/{created['id']}").json()
    assert draft["is_draft"] is True
    assert draft["status"] == "lawyer_approved"


def test_review_endpoint_returns_findings(client: TestClient) -> None:
    created = _create_draft(client)
    response = client.get(f"/api/v1/legal-drafting/drafts/{created['id']}/review")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_history_endpoint_returns_entries(client: TestClient) -> None:
    created = _create_draft(client)
    response = client.get(f"/api/v1/legal-drafting/drafts/{created['id']}/history")
    assert response.status_code == 200
    assert response.json()[0]["action"] == "created"


def test_export_html_returns_html_content_type(client: TestClient) -> None:
    created = _create_draft(client)
    response = client.get(
        f"/api/v1/legal-drafting/drafts/{created['id']}/export", params={"format": "html"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_export_docx_returns_docx_content_type(client: TestClient) -> None:
    created = _create_draft(client)
    response = client.get(
        f"/api/v1/legal-drafting/drafts/{created['id']}/export", params={"format": "docx"}
    )
    assert response.status_code == 200
    assert "wordprocessingml" in response.headers["content-type"]


def test_export_pdf_returns_pdf_content_type(client: TestClient) -> None:
    created = _create_draft(client)
    response = client.get(
        f"/api/v1/legal-drafting/drafts/{created['id']}/export", params={"format": "pdf"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_export_unknown_format_returns_400(client: TestClient) -> None:
    created = _create_draft(client)
    response = client.get(
        f"/api/v1/legal-drafting/drafts/{created['id']}/export", params={"format": "xml"}
    )
    assert response.status_code == 400


def test_create_draft_unknown_document_type_returns_400(client: TestClient) -> None:
    response = client.post(
        "/api/v1/legal-drafting/drafts", json={"document_type": "not-a-real-type"}
    )
    assert response.status_code == 400
