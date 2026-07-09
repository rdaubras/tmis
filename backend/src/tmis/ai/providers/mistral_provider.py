from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities


class MistralProvider:
    """Implements `ProviderPort` for Mistral models.

    Sprint 2 scope: deterministic echo response, no real network call (see
    `OpenAIProvider` for the rationale).
    """

    provider_name = "mistral"
    capabilities = ProviderCapabilities(supports_completion=True, supports_streaming=False)
    default_model = "mistral-large-latest"

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
