import pytest

from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities
from tmis.ai_fabric.batch.engine import BatchProcessor
from tmis.ai_fabric.batch.schemas import BatchRequest
from tmis.ai_fabric.streaming.engine import StreamAggregator, StreamingService


class _StubProvider:
    provider_name = "stub"
    capabilities = ProviderCapabilities()

    async def complete(self, prompt: str, *, model: str | None = None) -> ModelResponse:
        return ModelResponse(text=f"réponse à: {prompt}", provider="stub", model=model or "stub-1")


@pytest.mark.asyncio
async def test_streaming_service_yields_a_single_final_chunk_for_non_streaming_provider() -> None:
    service = StreamingService()
    provider = _StubProvider()

    chunks = [c async for c in service.stream(provider, "bonjour")]

    assert len(chunks) == 1
    assert chunks[0].is_final is True
    assert chunks[0].text == "réponse à: bonjour"


@pytest.mark.asyncio
async def test_stream_aggregator_collects_chunks_into_final_text() -> None:
    service = StreamingService()
    provider = _StubProvider()
    aggregator = StreamAggregator()

    collected = await aggregator.collect(service.stream(provider, "bonjour"))

    assert collected == "réponse à: bonjour"


@pytest.mark.asyncio
async def test_batch_processor_runs_every_request_and_preserves_ids() -> None:
    processor = BatchProcessor()
    requests = [
        BatchRequest("r1", "question 1", "gpt-x"),
        BatchRequest("r2", "question 2", "gpt-x"),
    ]

    async def _executor(request: BatchRequest) -> str:
        return f"answer to {request.prompt}"

    results = await processor.run_batch(requests, _executor)

    assert {r.request_id for r in results} == {"r1", "r2"}
    assert all(r.succeeded for r in results)


@pytest.mark.asyncio
async def test_batch_processor_isolates_a_failing_request() -> None:
    processor = BatchProcessor()
    requests = [BatchRequest("ok", "q", "gpt-x"), BatchRequest("bad", "q", "gpt-x")]

    async def _executor(request: BatchRequest) -> str:
        if request.request_id == "bad":
            raise ValueError("boom")
        return "fine"

    results = await processor.run_batch(requests, _executor)

    ok_result = next(r for r in results if r.request_id == "ok")
    bad_result = next(r for r in results if r.request_id == "bad")
    assert ok_result.succeeded is True
    assert bad_result.succeeded is False
    assert "boom" in (bad_result.error or "")
