from tmis.domain.shared.ports import ModelResponse


class LocalModelProvider:
    """Implements `ModelProviderPort` for a self-hosted open-source model.

    Wiring of the actual inference call (e.g. via vLLM/Ollama) is
    implemented in a future sprint (see docs/09-roadmap-30-sprints.md); this
    Sprint 1 stub establishes the interchangeability seam so a cabinet can
    opt for a fully self-hosted, data-sovereign deployment.
    """

    provider_name = "local"

    def __init__(self, model: str = "llama-3-70b-instruct") -> None:
        self._model = model

    async def complete(self, prompt: str, **params: object) -> ModelResponse:
        raise NotImplementedError("Local completion wiring is scheduled for a future sprint.")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Local embeddings wiring is scheduled for a future sprint.")
