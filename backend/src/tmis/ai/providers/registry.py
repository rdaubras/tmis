from tmis.ai.providers.anthropic_provider import AnthropicProvider
from tmis.ai.providers.local_provider import LocalProvider
from tmis.ai.providers.mistral_provider import MistralProvider
from tmis.ai.providers.openai_provider import OpenAIProvider
from tmis.ai.providers.ports import ProviderPort


class ProviderRegistry:
    """Resolves a `ProviderPort` implementation by configuration key.

    This is the seam through which `TMISKernel` obtains a model provider,
    keeping every caller vendor-agnostic. Register a new provider with
    `register()` instead of editing call sites (see
    docs/13-guides-extension.md).
    """

    def __init__(self) -> None:
        self._providers: dict[str, ProviderPort] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "mistral": MistralProvider(),
            "local": LocalProvider(),
        }

    def register(self, name: str, provider: ProviderPort) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> ProviderPort:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ValueError(f"Unknown model provider: {name!r}") from exc

    def list_names(self) -> list[str]:
        return list(self._providers)
