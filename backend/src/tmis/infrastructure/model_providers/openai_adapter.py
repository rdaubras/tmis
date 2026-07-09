from tmis.domain.shared.ports import ModelResponse


class OpenAIModelProvider:
    """Implements `ModelProviderPort` for OpenAI models.

    Wiring of the actual SDK call is implemented in a future sprint
    (see docs/09-roadmap-30-sprints.md); this Sprint 1 stub establishes the
    interchangeability seam.
    """

    provider_name = "openai"

    def __init__(self, model: str = "gpt-4o") -> None:
        self._model = model

    async def complete(self, prompt: str, **params: object) -> ModelResponse:
        raise NotImplementedError("OpenAI completion wiring is scheduled for a future sprint.")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("OpenAI embeddings wiring is scheduled for a future sprint.")
