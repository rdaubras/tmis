from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ResearchQuery:
    """A user's raw search request, normalized and enriched by the Query
    Engine before it reaches the Research Orchestrator (see
    docs/21-legal-research.md)."""

    raw_text: str
    normalized_text: str
    language: str | None
    keywords: tuple[str, ...] = field(default_factory=tuple)
    expanded_terms: tuple[str, ...] = field(default_factory=tuple)
    filters: dict[str, object] = field(default_factory=dict)

    @property
    def search_text(self) -> str:
        """The text actually sent to connectors: normalized text plus any
        expansion terms not already implied by it."""
        extra = [t for t in self.expanded_terms if t.lower() not in self.normalized_text.lower()]
        return " ".join([self.normalized_text, *extra]).strip()
