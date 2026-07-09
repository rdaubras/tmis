from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """A single, versioned prompt. `PromptRegistry` keeps every version
    ever registered under the same `id` (its history)."""

    id: str
    version: int
    category: str
    template: str
    variables: tuple[str, ...] = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def render(self, **kwargs: str) -> str:
        missing = [name for name in self.variables if name not in kwargs]
        if missing:
            raise ValueError(f"Missing variables for prompt {self.id!r}: {missing}")
        return self.template.format(**kwargs)
