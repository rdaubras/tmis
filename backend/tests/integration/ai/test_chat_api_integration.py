import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tmis.ai.kernel.bootstrap import get_kernel
from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities
from tmis.case_intelligence.bootstrap import get_case_intelligence_workflow
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
    workflow = get_case_intelligence_workflow()
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
