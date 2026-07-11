import re

from tmis.ai_governance.bias_detection.schemas import BiasFinding, new_bias_finding_id

_GENERALIZATION_PATTERN = re.compile(
    r"\b(les femmes|les hommes|les jeunes|les personnes âgées|les étrangers)\s+"
    r"(sont|ont tendance à|font)\b",
    re.IGNORECASE,
)


class GeneralizationBiasDetector:
    """Default detector shipped with the engine: flags sentences that
    generalize a behavior to an entire demographic group — a
    deterministic, explainable heuristic, not a model call. Extra
    detectors are registered via `BiasDetectionEngine.register()`
    without touching this class."""

    name = "generalization"

    def detect(self, text: str) -> list[BiasFinding]:
        findings: list[BiasFinding] = []
        for match in _GENERALIZATION_PATTERN.finditer(text):
            findings.append(
                BiasFinding(
                    id=new_bias_finding_id(),
                    detector_name=self.name,
                    category="generalization",
                    excerpt=match.group(0),
                    description="Généralisation potentiellement biaisée détectée",
                    explanation=(
                        f"L'expression {match.group(0)!r} généralise un comportement à un "
                        "groupe entier, ce qui peut introduire un biais dans la production."
                    ),
                )
            )
        return findings
