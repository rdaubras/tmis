from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OptimizedPrompt:
    """Result of adapting a rendered prompt to a specific target model."""

    text: str
    truncated: bool
    estimated_tokens: int
