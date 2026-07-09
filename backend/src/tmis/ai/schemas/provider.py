from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ModelMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ModelResponse:
    """Normalized response returned by every `ProviderPort` implementation,
    regardless of the underlying vendor SDK."""

    text: str
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    raw: dict[str, object] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass(frozen=True, slots=True)
class ProviderCapabilities:
    """Advertises what a provider adapter can do, so the Kernel/registry can
    pick a suitable provider without hardcoding vendor knowledge."""

    supports_completion: bool = True
    supports_embeddings: bool = False
    supports_streaming: bool = False
