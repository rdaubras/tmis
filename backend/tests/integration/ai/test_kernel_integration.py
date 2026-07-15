import uuid
from collections.abc import AsyncIterator

import pytest

from tmis.ai.guardrails.exceptions import GuardrailViolation
from tmis.ai.kernel import TMISKernel
from tmis.ai.schemas.agent import AgentInput, AgentOutput, AgentPort
from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities


class _CountingProvider:
    provider_name = "counting"
    capabilities = ProviderCapabilities()
    default_model = "counting-model"

    def __init__(self) -> None:
        self.call_count = 0

    async def complete(self, prompt: str, *, model: str | None = None) -> ModelResponse:
        self.call_count += 1
        return ModelResponse(
            text=f"response #{self.call_count}",
            provider=self.provider_name,
            model=model or self.default_model,
            prompt_tokens=1,
            completion_tokens=1,
        )

    async def complete_stream(
        self, prompt: str, *, model: str | None = None
    ) -> AsyncIterator[str]:
        self.call_count += 1
        for word in ("chunk-a", "chunk-b", "chunk-c"):
            yield word


class _EchoAgent:
    name = "echo"

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        return AgentOutput(result={"echo": agent_input.context})


@pytest.mark.asyncio
async def test_complete_uses_cache_on_second_identical_call() -> None:
    kernel = TMISKernel()
    provider = _CountingProvider()
    kernel.provider_registry.register("counting", provider)

    first = await kernel.complete("Bonjour", provider="counting")
    second = await kernel.complete("Bonjour", provider="counting")

    assert provider.call_count == 1
    assert first.text == second.text == "response #1"


@pytest.mark.asyncio
async def test_complete_bypasses_cache_when_use_cache_false() -> None:
    kernel = TMISKernel()
    provider = _CountingProvider()
    kernel.provider_registry.register("counting", provider)

    await kernel.complete("Bonjour", provider="counting", use_cache=False)
    await kernel.complete("Bonjour", provider="counting", use_cache=False)

    assert provider.call_count == 2


@pytest.mark.asyncio
async def test_complete_records_evaluation_metrics_once_per_provider_call() -> None:
    kernel = TMISKernel()
    provider = _CountingProvider()
    kernel.provider_registry.register("counting", provider)

    await kernel.complete("Bonjour", provider="counting")
    await kernel.complete("Bonjour", provider="counting")  # cache hit, no new metric

    assert len(kernel.evaluator.in_memory_metrics) == 1


@pytest.mark.asyncio
async def test_complete_rejects_empty_prompt_via_guardrails() -> None:
    kernel = TMISKernel()
    with pytest.raises(GuardrailViolation):
        await kernel.complete("   ")


@pytest.mark.asyncio
async def test_search_connectors_uses_cache() -> None:
    kernel = TMISKernel()
    first = await kernel.search_connectors("dommage")
    second = await kernel.search_connectors("dommage")
    assert [d.id for d in first] == [d.id for d in second]


def test_register_and_get_agent() -> None:
    kernel = TMISKernel()
    agent: AgentPort = _EchoAgent()
    kernel.register_agent("echo", agent)
    assert kernel.get_agent("echo") is agent
    assert kernel.list_agents() == ["echo"]


def test_get_unknown_agent_raises() -> None:
    kernel = TMISKernel()
    with pytest.raises(ValueError, match="Unknown agent"):
        kernel.get_agent("does-not-exist")


def test_kernel_registers_demo_workflow_on_init() -> None:
    kernel = TMISKernel()
    assert "kernel_demo" in kernel.list_workflows()


@pytest.mark.asyncio
async def test_complete_stream_yields_every_chunk_in_order() -> None:
    kernel = TMISKernel()
    provider = _CountingProvider()
    kernel.provider_registry.register("counting", provider)

    chunks = [
        chunk async for chunk in kernel.complete_stream("Bonjour", provider="counting")
    ]

    assert chunks == ["chunk-a", "chunk-b", "chunk-c"]


@pytest.mark.asyncio
async def test_complete_stream_rejects_empty_prompt_via_guardrails() -> None:
    kernel = TMISKernel()
    with pytest.raises(GuardrailViolation):
        async for _ in kernel.complete_stream("   "):
            pass


@pytest.mark.asyncio
async def test_complete_stream_does_not_log_to_conversation_memory_mid_stream() -> None:
    """"Jamais chunk par chunk": history must stay empty while the
    generator is still being consumed, and only gain the assembled
    assistant turn once it is fully drained."""
    kernel = TMISKernel()
    provider = _CountingProvider()
    kernel.provider_registry.register("counting", provider)
    conversation_id = uuid.uuid4()

    stream = kernel.complete_stream("Bonjour", provider="counting", conversation_id=conversation_id)
    first_chunk = await stream.__anext__()
    assert first_chunk == "chunk-a"
    assert await kernel.conversation_memory.get_history(conversation_id) == []

    async for _ in stream:
        pass

    assert await kernel.conversation_memory.get_history(conversation_id) == [
        "assistant: chunk-achunk-bchunk-c"
    ]


@pytest.mark.asyncio
async def test_complete_stream_without_conversation_id_does_not_touch_memory() -> None:
    kernel = TMISKernel()
    provider = _CountingProvider()
    kernel.provider_registry.register("counting", provider)
    conversation_id = uuid.uuid4()  # never passed to complete_stream below

    async for _ in kernel.complete_stream("Bonjour", provider="counting"):
        pass

    assert await kernel.conversation_memory.get_history(conversation_id) == []


@pytest.mark.asyncio
async def test_complete_unchanged_signature_still_works_alongside_complete_stream() -> None:
    """`complete()` remains untouched by this sprint: same call, same
    return type, usable on the same `TMISKernel` instance that also
    exposes `complete_stream()`."""
    kernel = TMISKernel()
    provider = _CountingProvider()
    kernel.provider_registry.register("counting", provider)

    response = await kernel.complete("Bonjour", provider="counting")

    assert isinstance(response, ModelResponse)
    assert response.text == "response #1"
