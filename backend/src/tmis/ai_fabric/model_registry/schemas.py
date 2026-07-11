from dataclasses import dataclass, field

from tmis.ai_fabric.capabilities.schemas import Capability
from tmis.ai_fabric.model_profiles.schemas import ModelProfile


@dataclass(slots=True)
class ModelDescriptor:
    """The sprint's "MODEL REGISTRY" spec: nom, version, fournisseur,
    coût, latence, contexte maximal, capacités, disponibilité, score
    qualité, score juridique, score rédaction, score recherche, score
    raisonnement. All scores are in `[0, 1]`."""

    name: str
    version: str
    provider: str
    cost_per_1k_tokens_usd: float
    avg_latency_ms: float
    max_context_tokens: int
    capabilities: frozenset[Capability]
    profiles: frozenset[ModelProfile] = field(default_factory=frozenset)
    availability: bool = True
    quality_score: float = 0.5
    legal_score: float = 0.5
    drafting_score: float = 0.5
    research_score: float = 0.5
    reasoning_score: float = 0.5
