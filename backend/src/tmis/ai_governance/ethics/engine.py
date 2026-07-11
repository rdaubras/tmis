import re

from tmis.ai_governance.ethics.schemas import EthicsFinding, new_ethics_finding_id

_OVERPROMISE_PATTERN = re.compile(
    r"\b(il est garanti que|vous gagnerez certainement|à coup sûr|sans aucun doute possible)\b",
    re.IGNORECASE,
)


class EthicsEngine:
    """The sprint's "ETHICS" module: a deterministic, extensible
    screening for content that raises a professional-responsibility
    concern — e.g. presenting a judicial outcome as guaranteed, which
    bar deontology rules typically forbid. Advisory only: it never
    blocks a production, it raises an explainable finding for human
    review."""

    def screen(self, text: str) -> list[EthicsFinding]:
        findings: list[EthicsFinding] = []
        for match in _OVERPROMISE_PATTERN.finditer(text):
            findings.append(
                EthicsFinding(
                    id=new_ethics_finding_id(),
                    category="overpromising",
                    excerpt=match.group(0),
                    description="Formulation présentant une issue judiciaire comme certaine",
                    explanation=(
                        f"L'expression {match.group(0)!r} promet un résultat de manière "
                        "absolue, ce que les règles déontologiques encadrant le conseil "
                        "juridique interdisent généralement."
                    ),
                )
            )
        return findings
