from enum import StrEnum


class Capability(StrEnum):
    """Low-level technical capabilities a model may support — distinct
    from `tmis.ai_fabric.model_profiles.ModelProfile`, which is the
    higher-level semantic specialization used to match a task to a
    model (see docs/73-architecture-ai-fabric.md)."""

    TEXT_COMPLETION = "text_completion"
    EMBEDDINGS = "embeddings"
    OCR = "ocr"
    VISION = "vision"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    LONG_CONTEXT = "long_context"
