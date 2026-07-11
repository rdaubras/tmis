from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.model_profiles.schemas import ModelProfile
from tmis.ai_fabric.model_registry.ports import ModelRegistryPort
from tmis.ai_fabric.model_registry.schemas import ModelDescriptor

_DEFAULT_MODELS: tuple[ModelDescriptor, ...] = (
    ModelDescriptor(
        name="gpt-4-legal",
        version="2024-08",
        provider="openai",
        cost_per_1k_tokens_usd=0.03,
        avg_latency_ms=1200,
        max_context_tokens=128_000,
        capabilities=frozenset(
            {Capability.TEXT_COMPLETION, Capability.FUNCTION_CALLING, Capability.LONG_CONTEXT}
        ),
        profiles=frozenset(
            {ModelProfile.REASONING, ModelProfile.DRAFTING, ModelProfile.SYNTHESIS}
        ),
        quality_score=0.90,
        legal_score=0.85,
        drafting_score=0.88,
        research_score=0.80,
        reasoning_score=0.87,
    ),
    ModelDescriptor(
        name="claude-legal",
        version="4.5",
        provider="anthropic",
        cost_per_1k_tokens_usd=0.024,
        avg_latency_ms=1000,
        max_context_tokens=200_000,
        capabilities=frozenset(
            {Capability.TEXT_COMPLETION, Capability.LONG_CONTEXT, Capability.STREAMING}
        ),
        profiles=frozenset(
            {ModelProfile.REASONING, ModelProfile.DRAFTING, ModelProfile.SYNTHESIS}
        ),
        quality_score=0.91,
        legal_score=0.88,
        drafting_score=0.90,
        research_score=0.82,
        reasoning_score=0.90,
    ),
    ModelDescriptor(
        name="mistral-fast",
        version="large-2",
        provider="mistral",
        cost_per_1k_tokens_usd=0.002,
        avg_latency_ms=400,
        max_context_tokens=32_000,
        capabilities=frozenset({Capability.TEXT_COMPLETION}),
        profiles=frozenset({ModelProfile.CLASSIFICATION, ModelProfile.TRANSLATION}),
        quality_score=0.65,
        legal_score=0.55,
        drafting_score=0.55,
        research_score=0.55,
        reasoning_score=0.55,
    ),
    ModelDescriptor(
        name="local-ocr",
        version="1.0",
        provider="local",
        cost_per_1k_tokens_usd=0.0,
        avg_latency_ms=2000,
        max_context_tokens=4_000,
        capabilities=frozenset({Capability.OCR}),
        profiles=frozenset({ModelProfile.OCR}),
        quality_score=0.70,
        legal_score=0.50,
        drafting_score=0.30,
        research_score=0.40,
        reasoning_score=0.30,
    ),
    ModelDescriptor(
        name="local-vision",
        version="1.0",
        provider="local",
        cost_per_1k_tokens_usd=0.0,
        avg_latency_ms=2500,
        max_context_tokens=4_000,
        capabilities=frozenset({Capability.VISION}),
        profiles=frozenset({ModelProfile.VISION}),
        quality_score=0.68,
        legal_score=0.45,
        drafting_score=0.30,
        research_score=0.40,
        reasoning_score=0.30,
    ),
    ModelDescriptor(
        name="embed-small",
        version="3-small",
        provider="openai",
        cost_per_1k_tokens_usd=0.0001,
        avg_latency_ms=200,
        max_context_tokens=8_000,
        capabilities=frozenset({Capability.EMBEDDINGS}),
        profiles=frozenset({ModelProfile.EMBEDDINGS}),
        quality_score=0.75,
        legal_score=0.50,
        drafting_score=0.20,
        research_score=0.60,
        reasoning_score=0.20,
    ),
)


def seed_default_models(registry: ModelRegistryPort) -> None:
    """Registers a representative catalog spanning every provider
    already wired in `tmis.ai.providers.registry.ProviderRegistry`
    (openai/anthropic/mistral/local) and every `ModelProfile`, so the
    Fabric has real routing choices out of the box instead of an
    empty registry."""
    for descriptor in _DEFAULT_MODELS:
        registry.register(descriptor)
