from collections.abc import AsyncIterator

from tmis.ai.providers.ports import ProviderPort
from tmis.ai_fabric.streaming.schemas import StreamChunk


class StreamingService:
    """The sprint's "STREAMING" module: exposes a uniform
    chunk-by-chunk interface regardless of whether the underlying
    provider actually streams. No provider stub in
    `tmis.ai.providers` (Sprint 2) performs a real streaming network
    call yet, so a non-streaming provider's full response is
    represented as a single final chunk — callers never special-case
    "no streaming support"."""

    async def stream(
        self, provider: ProviderPort, prompt: str, *, model: str | None = None
    ) -> AsyncIterator[StreamChunk]:
        response = await provider.complete(prompt, model=model)
        yield StreamChunk(text=response.text, is_final=True)


class StreamAggregator:
    """Collects streamed chunks back into the final assembled text."""

    def __init__(self) -> None:
        self._buffer: list[str] = []

    def append(self, chunk: StreamChunk) -> str:
        self._buffer.append(chunk.text)
        return "".join(self._buffer)

    async def collect(self, chunks: AsyncIterator[StreamChunk]) -> str:
        async for chunk in chunks:
            self.append(chunk)
        return "".join(self._buffer)
