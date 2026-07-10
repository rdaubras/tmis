"""A tiny, hand-curated legal synonym dictionary used for query expansion.

Sprint 5 scope: enough entries to demonstrate expansion end-to-end; a
thesaurus-backed or embedding-based expander can replace this behind
`QueryEnginePort` without touching the Research Orchestrator.
"""

LEGAL_SYNONYMS: dict[str, tuple[str, ...]] = {
    "licenciement": ("rupture du contrat de travail", "congédiement"),
    "bail": ("contrat de location", "location"),
    "contrat": ("convention", "accord"),
    "clause": ("stipulation",),
    "responsabilité": ("réparation du dommage", "faute"),
    "divorce": ("dissolution du mariage",),
    "préjudice": ("dommage",),
}


def expand(keywords: tuple[str, ...]) -> tuple[str, ...]:
    expanded: list[str] = []
    for keyword in keywords:
        for synonym in LEGAL_SYNONYMS.get(keyword.lower(), ()):
            if synonym not in expanded:
                expanded.append(synonym)
    return tuple(expanded)
