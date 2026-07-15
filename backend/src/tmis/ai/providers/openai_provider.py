from collections.abc import AsyncIterator

from tmis.ai.schemas.provider import ModelResponse, ProviderCapabilities


class OpenAIProvider:
    """Implements `ProviderPort` for OpenAI models.

    Sprint 2 scope: no real network call is made yet (see
    docs/09-roadmap-30-sprints.md — the actual SDK wiring is business
    functionality, out of scope for the AI Kernel). `complete()` returns a
    deterministic, clearly-tagged echo so the Kernel, the LangGraph demo
    workflow and the evaluation pipeline are fully exercisable today.
    """

    provider_name = "openai"
    capabilities = ProviderCapabilities(supports_completion=True, supports_streaming=True)
    default_model = "gpt-4o"

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
        """Word-by-word chunking of the deterministic `complete()` text.

        `capabilities.supports_streaming` is `True` for this provider, but
        no real vendor SDK call exists yet anywhere in this adapter (see
        `complete()` docstring) — there is no native SDK stream to
        forward. Chunking honors the already-declared capability without
        pretending to wrap a live SDK stream (see docs/160-architecture-
        chat-ia.md).
        """
        response = await self.complete(prompt, model=model)
        words = response.text.split(" ")
        for index, word in enumerate(words):
            yield word if index == len(words) - 1 else f"{word} "
