from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ModelResponse:
    text: str
    provider: str
    model: str


class ModelProviderPort(Protocol):
    """Port implemented by every interchangeable AI model provider adapter."""

    async def complete(self, prompt: str, **params: object) -> ModelResponse: ...

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True, slots=True)
class Citation:
    source_id: str
    connector: str
    excerpt: str
    reference: str


@dataclass(frozen=True, slots=True)
class LegalDocument:
    id: str
    title: str
    content: str
    connector: str


class LegalSourceConnectorPort(Protocol):
    """Port implemented by every interchangeable legal source connector."""

    async def search(
        self, query: str, filters: dict[str, object] | None = None
    ) -> list[LegalDocument]: ...

    async def fetch(self, document_id: str) -> LegalDocument | None: ...
