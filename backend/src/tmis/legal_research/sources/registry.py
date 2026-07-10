from tmis.legal_research.sources.schemas import SourceCategory, SourceDescriptor

_DEFAULT_SOURCES: list[SourceDescriptor] = [
    SourceDescriptor(
        connector_name="codes",
        category=SourceCategory.LEGISLATION,
        display_name="Codes et textes législatifs",
        authority_score=1.0,
        description="Codes et textes en vigueur.",
    ),
    SourceDescriptor(
        connector_name="jurisprudence",
        category=SourceCategory.JURISPRUDENCE,
        display_name="Jurisprudence",
        authority_score=0.9,
        description="Décisions de justice.",
    ),
    SourceDescriptor(
        connector_name="doctrine",
        category=SourceCategory.DOCTRINE,
        display_name="Doctrine",
        authority_score=0.6,
        description="Articles et commentaires doctrinaux.",
    ),
    SourceDescriptor(
        connector_name="internal_documentation",
        category=SourceCategory.INTERNAL_DOCUMENTATION,
        display_name="Documentation interne du cabinet",
        authority_score=0.5,
        description="Notes et mémos internes au cabinet.",
    ),
    SourceDescriptor(
        connector_name="private_database",
        category=SourceCategory.PRIVATE_DATABASE,
        display_name="Base privée sous licence",
        authority_score=0.8,
        description="Base documentaire privée à laquelle le cabinet a souscrit.",
    ),
]


class SourceRegistry:
    """Catalog of known sources, keyed by connector name (see
    docs/21-legal-research.md — Source Normalizer / Ranking Engine).

    Unknown connectors (e.g. a newly registered one nobody described yet)
    fall back to a neutral authority score rather than raising, so the
    Ranking Engine never breaks on an unregistered connector.
    """

    _DEFAULT_AUTHORITY_SCORE = 0.3

    def __init__(self, sources: list[SourceDescriptor] | None = None) -> None:
        entries = sources if sources is not None else _DEFAULT_SOURCES
        self._by_connector: dict[str, SourceDescriptor] = {s.connector_name: s for s in entries}

    def register(self, descriptor: SourceDescriptor) -> None:
        self._by_connector[descriptor.connector_name] = descriptor

    def get(self, connector_name: str) -> SourceDescriptor | None:
        return self._by_connector.get(connector_name)

    def authority_score(self, connector_name: str) -> float:
        descriptor = self._by_connector.get(connector_name)
        return descriptor.authority_score if descriptor else self._DEFAULT_AUTHORITY_SCORE

    def list_sources(self) -> list[SourceDescriptor]:
        return list(self._by_connector.values())
