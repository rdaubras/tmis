from collections.abc import AsyncIterator

from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities


class AnthropicProvider:
    """Implements `ProviderPort` for Anthropic models.

    Sprint 2 scope: deterministic echo response, no real network call (see
    `OpenAIProvider` for the rationale).
    """

    provider_name = "anthropic"
    capabilities = ProviderCapabilities(supports_completion=True, supports_streaming=True)
    default_model = "claude-sonnet-5"

    async def complete(self, prompt: str, *, model: str | None = None) -> ModelResponse:
        used_model = model or self.default_model
        prompt_tokens = len(prompt.split())
        text = f"[{self.provider_name}:{used_model}] {prompt}"
        return ModelResponse(
            text=text,
            provider=self.provider_name,
            model=used_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=prompt_tokens,
        )

    async def complete_stream(
        self, prompt: str, *, model: str | None = None
    ) -> AsyncIterator[str]:
        """Word-by-word chunking of the deterministic `complete()` text —
        see `OpenAIProvider.complete_stream` for the rationale (same
        `supports_streaming=True` capability, same absence of a real SDK
        call to forward)."""
        response = await self.complete(prompt, model=model)
        words = response.text.split(" ")
        for index, word in enumerate(words):
            yield word if index == len(words) - 1 else f"{word} "
