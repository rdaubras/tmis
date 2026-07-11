"""The sprint's "PROVIDER REGISTRY" — deliberately **not** a new
registry. `tmis.ai.providers.registry.ProviderRegistry` (Sprint 2)
already resolves a `ProviderPort` implementation by configuration key
(OpenAI/Anthropic/Mistral/local) and is the seam every provider call
in TMIS goes through. Duplicating it here would give the Fabric a
second, competing source of truth for "which providers exist" — so
`ai_fabric` reuses it wholesale. `tmis.ai_fabric.model_registry`
carries the additional per-model metadata (cost, latency, scores)
this sprint needs; `provider_registry` only needs to resolve the
callable adapter a chosen model's `provider` field names."""

from tmis.ai.providers.ports import ProviderPort
from tmis.ai.providers.registry import ProviderRegistry as FabricProviderRegistry

__all__ = ["FabricProviderRegistry", "ProviderPort"]
