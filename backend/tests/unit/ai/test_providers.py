import pytest

from tmis.ai.providers.anthropic_provider import AnthropicProvider
from tmis.ai.providers.local_provider import LocalProvider
from tmis.ai.providers.mistral_provider import MistralProvider
from tmis.ai.providers.openai_provider import OpenAIProvider
from tmis.ai.providers.registry import ProviderRegistry


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "provider_cls",
    [OpenAIProvider, AnthropicProvider, MistralProvider, LocalProvider],
)
async def test_provider_complete_is_deterministic_and_tagged(provider_cls: type) -> None:
    provider = provider_cls()
    response = await provider.complete("Bonjour")

    assert response.provider == provider.provider_name
    assert provider.provider_name in response.text
    assert response.model in response.text
    assert response.prompt_tokens == 1
    assert response.total_tokens == response.prompt_tokens + response.completion_tokens


@pytest.mark.asyncio
async def test_provider_complete_uses_requested_model() -> None:
    provider = OpenAIProvider()
    response = await provider.complete("test", model="gpt-4o-mini")
    assert response.model == "gpt-4o-mini"


def test_registry_returns_all_four_default_providers() -> None:
    registry = ProviderRegistry()
    assert set(registry.list_names()) == {"openai", "anthropic", "mistral", "local"}


def test_registry_get_unknown_provider_raises() -> None:
    registry = ProviderRegistry()
    with pytest.raises(ValueError, match="Unknown model provider"):
        registry.get("does-not-exist")


def test_registry_register_overrides_provider() -> None:
    registry = ProviderRegistry()
    custom = OpenAIProvider()
    registry.register("custom", custom)
    assert registry.get("custom") is custom


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_cls", [OpenAIProvider, AnthropicProvider])
async def test_streaming_provider_yields_more_than_one_chunk_and_reassembles_exactly(
    provider_cls: type,
) -> None:
    """`supports_streaming=True` providers chunk the deterministic
    `complete()` text word-by-word rather than falling back to a single
    chunk — see docs/160-architecture-chat-ia.md."""
    provider = provider_cls()
    expected = await provider.complete("Bonjour cher confrere")

    chunks = [chunk async for chunk in provider.complete_stream("Bonjour cher confrere")]

    assert len(chunks) > 1
    assert "".join(chunks) == expected.text


@pytest.mark.asyncio
@pytest.mark.parametrize("provider_cls", [MistralProvider, LocalProvider])
async def test_non_streaming_provider_falls_back_to_a_single_chunk(
    provider_cls: type,
) -> None:
    """`supports_streaming=False` providers never fail `complete_stream`:
    they call `complete()` and yield the entire text as one chunk."""
    provider = provider_cls()
    expected = await provider.complete("Bonjour cher confrere")

    chunks = [chunk async for chunk in provider.complete_stream("Bonjour cher confrere")]

    assert chunks == [expected.text]


@pytest.mark.asyncio
async def test_streaming_provider_honors_requested_model() -> None:
    provider = OpenAIProvider()
    chunks = [chunk async for chunk in provider.complete_stream("test", model="gpt-4o-mini")]
    assert "gpt-4o-mini" in "".join(chunks)
