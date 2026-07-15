from collections.abc import AsyncIterator

from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities


class LocalProvider:
    """Implements `ProviderPort` for a self-hosted open-source model
    (e.g. served via vLLM/Ollama), for cabinets requiring full data
    sovereignty.

    Sprint 2 scope: deterministic echo response, no real inference call
    (see `OpenAIProvider` for the rationale).
    """

    provider_name = "local"
    capabilities = ProviderCapabilities(supports_completion=True, supports_streaming=False)
    default_model = "llama-3-70b-instruct"

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
        """`capabilities.supports_streaming` is `False` for this provider:
        fallback that calls `complete()` and yields the full text as a
        single chunk — never a failure."""
        response = await self.complete(prompt, model=model)
        yield response.text
