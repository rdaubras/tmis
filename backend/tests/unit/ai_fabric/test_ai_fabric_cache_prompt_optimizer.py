import pytest

from tmis.ai.cache.in_memory_cache import InMemoryCache
from tmis.ai.prompts.registry import PromptRegistry
from tmis.ai_fabric.cache.engine import ResponseCache
from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor
from tmis.ai_fabric.prompt_optimizer.engine import PromptOptimizer


@pytest.mark.asyncio
async def test_response_cache_miss_then_hit() -> None:
    cache = ResponseCache(InMemoryCache())

    assert await cache.get("drafting", "gpt-x", "rédige un avis") is None

    await cache.set("drafting", "gpt-x", "rédige un avis", "voici l'avis")

    assert await cache.get("drafting", "gpt-x", "rédige un avis") == "voici l'avis"


@pytest.mark.asyncio
async def test_response_cache_is_keyed_by_task_type_model_and_prompt() -> None:
    cache = ResponseCache(InMemoryCache())
    await cache.set("drafting", "gpt-x", "prompt", "response-a")

    assert await cache.get("research", "gpt-x", "prompt") is None
    assert await cache.get("drafting", "claude-y", "prompt") is None


@pytest.mark.asyncio
async def test_response_cache_invalidate() -> None:
    cache = ResponseCache(InMemoryCache())
    await cache.set("drafting", "gpt-x", "prompt", "response")

    await cache.invalidate("drafting", "gpt-x", "prompt")

    assert await cache.get("drafting", "gpt-x", "prompt") is None


def test_prompt_optimizer_register_and_render() -> None:
    optimizer = PromptOptimizer(PromptRegistry())
    optimizer.register(
        "avis-bail",
        category="drafting",
        template="Rédige un avis sur {sujet}.",
        variables=("sujet",),
    )

    rendered = optimizer.render("avis-bail", sujet="le bail commercial")

    assert rendered == "Rédige un avis sur le bail commercial."


def test_prompt_optimizer_history_keeps_every_version() -> None:
    optimizer = PromptOptimizer(PromptRegistry())
    optimizer.register("p", category="c", template="v1")
    optimizer.register("p", category="c", template="v2")

    versions = optimizer.history("p")

    assert [v.version for v in versions] == [1, 2]


def _model(max_context_tokens: int) -> ModelDescriptor:
    return ModelDescriptor(
        name="gpt-x",
        version="1",
        provider="openai",
        cost_per_1k_tokens_usd=0.01,
        avg_latency_ms=500.0,
        max_context_tokens=max_context_tokens,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
        profiles=frozenset({ModelProfile.DRAFTING}),
    )


def test_adapt_for_model_leaves_short_prompt_untouched() -> None:
    optimizer = PromptOptimizer(PromptRegistry())

    result = optimizer.adapt_for_model("un prompt court", _model(max_context_tokens=1000))

    assert result.truncated is False
    assert result.text == "un prompt court"


def test_adapt_for_model_truncates_when_over_budget() -> None:
    optimizer = PromptOptimizer(PromptRegistry())
    long_prompt = " ".join(f"mot{i}" for i in range(100))

    result = optimizer.adapt_for_model(long_prompt, _model(max_context_tokens=520))

    assert result.truncated is True
    assert len(result.text.split()) <= 8
