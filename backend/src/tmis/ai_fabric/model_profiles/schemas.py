from enum import StrEnum

from tmis.ai_fabric.capabilities.schemas import Capability


class ModelProfile(StrEnum):
    """The sprint's "MODEL PROFILES" spec — a semantic specialization,
    independent from any one model's technical `Capability` set, so a
    profile's meaning can evolve without touching every model
    descriptor that declares it."""

    REASONING = "reasoning"
    DRAFTING = "drafting"
    TRANSLATION = "translation"
    SYNTHESIS = "synthesis"
    CODE = "code"
    OCR = "ocr"
    VISION = "vision"
    EMBEDDINGS = "embeddings"
    CLASSIFICATION = "classification"


_DEFAULT_CAPABILITIES: dict[ModelProfile, frozenset[Capability]] = {
    ModelProfile.REASONING: frozenset({Capability.TEXT_COMPLETION, Capability.LONG_CONTEXT}),
    ModelProfile.DRAFTING: frozenset({Capability.TEXT_COMPLETION}),
    ModelProfile.TRANSLATION: frozenset({Capability.TEXT_COMPLETION}),
    ModelProfile.SYNTHESIS: frozenset({Capability.TEXT_COMPLETION, Capability.LONG_CONTEXT}),
    ModelProfile.CODE: frozenset({Capability.TEXT_COMPLETION, Capability.FUNCTION_CALLING}),
    ModelProfile.OCR: frozenset({Capability.OCR}),
    ModelProfile.VISION: frozenset({Capability.VISION}),
    ModelProfile.EMBEDDINGS: frozenset({Capability.EMBEDDINGS}),
    ModelProfile.CLASSIFICATION: frozenset({Capability.TEXT_COMPLETION}),
}


def default_capabilities_for_profile(profile: ModelProfile) -> frozenset[Capability]:
    return _DEFAULT_CAPABILITIES[profile]
