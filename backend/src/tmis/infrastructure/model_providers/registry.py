from tmis.domain.shared.ports import ModelProviderPort
from tmis.infrastructure.model_providers.anthropic_adapter import AnthropicModelProvider
from tmis.infrastructure.model_providers.local_adapter import LocalModelProvider
from tmis.infrastructure.model_providers.mistral_adapter import MistralModelProvider
from tmis.infrastructure.model_providers.openai_adapter import OpenAIModelProvider

_PROVIDERS: dict[str, type[ModelProviderPort]] = {
    "openai": OpenAIModelProvider,
    "anthropic": AnthropicModelProvider,
    "mistral": MistralModelProvider,
    "local": LocalModelProvider,
}


def get_model_provider(name: str) -> ModelProviderPort:
    """Resolve a `ModelProviderPort` implementation by configuration key.

    This is the single seam through which agents and use cases obtain a
    model provider, keeping every caller vendor-agnostic.
    """
    try:
        provider_class = _PROVIDERS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown model provider: {name!r}") from exc
    return provider_class()
