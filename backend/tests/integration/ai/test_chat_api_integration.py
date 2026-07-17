import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities
from tmis.case_intelligence.bootstrap import (
    clear_case_intelligence_caches,
    get_shared_case_intelligence_workflow,
)
from tmis.main import app


class _ChunkingTestProvider:
    """Deterministic multi-chunk provider registered directly on the real
    `TMISKernel` singleton — the same test-double pattern already used by
    `tests/integration/ai/test_kernel_integration.py::_CountingProvider`
    (this repo never uses `app.dependency_overrides`, see the audit
    report)."""

    provider_name = "chat-test-provider"
    capabilities = ProviderCapabilities(supports_streaming=True)
    default_model = "chat-test-model"

    async def complete(self, prompt: str, *, model: str | None = None) -> ModelResponse:
        return ModelResponse(
            text=f"reponse a: {prompt}",
            provider=self.provider_name,
            model=model or self.default_model,
        )

    async def complete_stream(
        self, prompt: str, *, model: str | None = None
    ) -> AsyncIterator[str]:
        for word in ("Bonjour", " ", "confrere", ".") :
            yield word


def _parse_sse_chunks(body: str) -> list[str]:
    chunks: list[str] = []
    for block in body.split("\n\n"):
        if not block.startswith("data: "):
            continue
        import json

        payload: dict[str, Any] = json.loads(block[len("data: ") :])
        if "chunk" in payload:
            chunks.append(payload["chunk"])
    return chunks


@pytest.fixture(autouse=True)
def _clear_case_workflow_singleton() -> None:
    """The chat route composes `get_shared_case_intelligence_workflow()`
    (ADR-CASEINT-01, docs/19-case-intelligence.md: chat has no
    `firm_id` to scope by, so it stays on the legacy, non-firm-scoped,
    in-memory `CaseStorePort` — no database needed here at all, unlike
    `test_case_api.py`'s firm-scoped, persistent `SQLAlchemyCaseStore`).
    Reset it before each test so cases created by one test don't leak
    into another."""
    clear_case_intelligence_caches()


@pytest.fixture
def client() -> TestClient:
    kernel = get_kernel()
    kernel.provider_registry.register("chat-test-provider", _ChunkingTestProvider())
    return TestClient(app)


def test_chat_stream_returns_multiple_sse_chunks_and_a_done_event(client: TestClient) -> None:
    conversation_id = uuid.uuid4()

    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(conversation_id),
            "message": "Bonjour",
            "provider": "chat-test-provider",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    chunks = _parse_sse_chunks(response.text)
    assert chunks == ["Bonjour", " ", "confrere", "."]
    assert "event: done" in response.text


@pytest.mark.asyncio
async def test_chat_stream_persists_the_full_turn_scoped_per_conversation(
    client: TestClient,
) -> None:
    conversation_id = uuid.uuid4()
    other_conversation_id = uuid.uuid4()

    client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(conversation_id),
            "message": "Quelle est la procedure ?",
            "provider": "chat-test-provider",
        },
    )

    kernel = get_kernel()
    history = await kernel.conversation_memory.get_history(conversation_id)
    assert history == [
        "user: Quelle est la procedure ?",
        "assistant: Bonjour confrere.",
    ]
    assert await kernel.conversation_memory.get_history(other_conversation_id) == []


def test_chat_stream_with_unknown_case_id_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "Bonjour",
            "case_id": "does-not-exist",
            "provider": "chat-test-provider",
        },
    )

    assert response.status_code == 404


def test_chat_stream_with_known_case_id_injects_it_and_streams(client: TestClient) -> None:
    workflow = get_shared_case_intelligence_workflow()
    profile = workflow.case_store.get_or_create("case-chat-1", title="Dossier Chat")

    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "Ou en est ce dossier ?",
            "case_id": profile.case_id,
            "provider": "chat-test-provider",
        },
    )

    assert response.status_code == 200
    assert _parse_sse_chunks(response.text) == ["Bonjour", " ", "confrere", "."]


def test_chat_stream_rejects_empty_message_with_400(client: TestClient) -> None:
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "   ",
            "provider": "chat-test-provider",
        },
    )

    assert response.status_code == 400


def _parse_sse_event(body: str) -> dict[str, Any]:
    for block in body.split("\n\n"):
        if block.startswith("data: ") and block != "data: {}":
            import json

            return json.loads(block[len("data: ") :])  # type: ignore[no-any-return]
    raise AssertionError(f"No data event found in SSE body: {body!r}")


def test_chat_stream_research_mode_returns_a_single_event_with_results_and_citations(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "contrat de travail",
            "mode": "research",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: done" in response.text

    payload = _parse_sse_event(response.text)
    assert payload["result"]["query"] == "contrat de travail"
    assert payload["result"]["results"]
    assert payload["confidence"] in ("low", "medium", "high")
    assert isinstance(payload["citations"], list)
    assert len(payload["citations"]) == len(payload["result"]["results"])
    for citation in payload["citations"]:
        assert citation["source_id"]
        assert citation["connector"]
        assert citation["reference"]


def test_chat_stream_research_mode_with_no_result_still_returns_a_clean_event(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "xyzzyplugh1234 introuvable",
            "mode": "research",
        },
    )

    assert response.status_code == 200
    payload = _parse_sse_event(response.text)
    assert payload["result"]["results"] == []
    assert payload["confidence"] == "low"
    assert payload["citations"] == []


def test_chat_stream_research_mode_with_a_non_uuid_case_id_still_searches(
    client: TestClient,
) -> None:
    """`ChatMessageRequest.case_id` reuses `case_intelligence`'s free-form
    string ids (see `_research_agent_input`); one that doesn't parse as a
    UUID must not break research mode, it just isn't tagged onto the LRE
    history entry."""
    workflow = get_shared_case_intelligence_workflow()
    workflow.case_store.get_or_create("case-chat-research-1", title="Dossier Recherche")

    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "contrat de travail",
            "case_id": "case-chat-research-1",
            "mode": "research",
        },
    )

    assert response.status_code == 200
    payload = _parse_sse_event(response.text)
    assert payload["result"]["results"]


@pytest.mark.asyncio
async def test_chat_stream_research_mode_persists_the_turn(client: TestClient) -> None:
    conversation_id = uuid.uuid4()

    client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(conversation_id),
            "message": "non-concurrence",
            "mode": "research",
        },
    )

    kernel = get_kernel()
    history = await kernel.conversation_memory.get_history(conversation_id)
    assert history[0] == "user: non-concurrence"
    assert history[1].startswith("assistant: Recherche juridique")


def test_chat_stream_jurisprudence_mode_returns_a_single_event_with_comparison(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "contractuelle",
            "mode": "jurisprudence",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert "event: done" in response.text

    payload = _parse_sse_event(response.text)
    assert payload["result"]["query"] == "contractuelle"
    assert payload["result"]["results"]
    assert payload["result"]["connectors_used"] == ["jurisprudence"]
    assert "comparison" in payload["result"]
    assert "model" in payload["result"]
    assert payload["confidence"] in ("low", "medium", "high")
    assert isinstance(payload["citations"], list)
    assert len(payload["citations"]) == len(payload["result"]["results"])


def test_chat_stream_jurisprudence_mode_with_no_result_still_returns_a_clean_event(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "xyzzyplugh1234 introuvable",
            "mode": "jurisprudence",
        },
    )

    assert response.status_code == 200
    payload = _parse_sse_event(response.text)
    assert payload["result"]["results"] == []
    assert payload["result"]["comparison"] is None
    assert payload["confidence"] == "low"
    assert payload["citations"] == []


def test_chat_stream_jurisprudence_mode_with_a_non_uuid_case_id_still_searches(
    client: TestClient,
) -> None:
    workflow = get_shared_case_intelligence_workflow()
    workflow.case_store.get_or_create("case-chat-jurisprudence-1", title="Dossier Jurisprudence")

    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "contractuelle",
            "case_id": "case-chat-jurisprudence-1",
            "mode": "jurisprudence",
        },
    )

    assert response.status_code == 200
    payload = _parse_sse_event(response.text)
    assert payload["result"]["results"]


@pytest.mark.asyncio
async def test_chat_stream_jurisprudence_mode_persists_the_turn(client: TestClient) -> None:
    conversation_id = uuid.uuid4()

    client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(conversation_id),
            "message": "contractuelle",
            "mode": "jurisprudence",
        },
    )

    kernel = get_kernel()
    history = await kernel.conversation_memory.get_history(conversation_id)
    assert history[0] == "user: contractuelle"
    assert history[1].startswith("assistant: Comparaison de jurisprudence")


def test_chat_stream_with_unknown_case_id_returns_404_for_jurisprudence_mode(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "contractuelle",
            "case_id": "does-not-exist",
            "mode": "jurisprudence",
        },
    )

    assert response.status_code == 404


def test_chat_stream_general_mode_still_works_unchanged(client: TestClient) -> None:
    """Same request shape as Sprint 32's tests above, `mode` simply
    defaulting to `"general"` — proves Sprint 33's additive change left
    the pre-existing behavior untouched."""
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "conversation_id": str(uuid.uuid4()),
            "message": "Bonjour",
            "provider": "chat-test-provider",
        },
    )

    assert response.status_code == 200
    assert _parse_sse_chunks(response.text) == ["Bonjour", " ", "confrere", "."]
