from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Explanation:
    """Why the reasoning run reached what it reached — attached to every
    `ReasoningSession` (see docs/25-legal-reasoning.md — Explanations)."""

    reasoning_steps: tuple[str, ...]
    components_used: tuple[str, ...]
    references: tuple[str, ...]
    hypotheses_considered: tuple[str, ...]
    limitations: tuple[str, ...]
