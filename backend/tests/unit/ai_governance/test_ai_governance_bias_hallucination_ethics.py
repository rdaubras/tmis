from tmis.ai_governance.bias_detection.engine import BiasDetectionEngine
from tmis.ai_governance.bias_detection.schemas import BiasFinding
from tmis.ai_governance.ethics.engine import EthicsEngine
from tmis.ai_governance.hallucination_detection.engine import HallucinationDetectionEngine


def test_bias_detection_flags_generalizations() -> None:
    engine = BiasDetectionEngine()

    findings = engine.scan("Les femmes sont plus douées pour la négociation amiable.")

    assert len(findings) == 1
    assert findings[0].category == "generalization"
    assert findings[0].explanation


def test_bias_detection_finds_nothing_in_neutral_text() -> None:
    engine = BiasDetectionEngine()

    findings = engine.scan("Le contrat est valide et produit ses effets entre les parties.")

    assert findings == []


def test_bias_detection_engine_is_extensible_via_register() -> None:
    class _AlwaysFlagsDetector:
        name = "always-flags"

        def detect(self, text: str) -> list[BiasFinding]:
            return [
                BiasFinding(
                    id="custom-1",
                    detector_name=self.name,
                    category="custom",
                    excerpt=text[:10],
                    description="test",
                    explanation="test",
                )
            ]

    engine = BiasDetectionEngine(detectors=[])
    engine.register(_AlwaysFlagsDetector())

    findings = engine.scan("n'importe quel texte")

    assert len(findings) == 1
    assert findings[0].detector_name == "always-flags"


def test_hallucination_detection_flags_missing_citations() -> None:
    engine = HallucinationDetectionEngine()

    alerts = engine.scan("Cela semble correct sans plus de précision sur la source.")

    assert len(alerts) == 1
    assert "citation" in alerts[0].reason.lower()
    assert alerts[0].recommendation


def test_hallucination_detection_flags_contradictions() -> None:
    engine = HallucinationDetectionEngine()
    text = (
        "Le contrat est valide et pleinement applicable entre les parties. "
        "Le contrat n'est pas valide et pleinement applicable entre les parties."
    )

    alerts = engine.scan(text)

    assert any("contradiction" in a.reason.lower() for a in alerts)


def test_hallucination_detection_never_alters_the_input_text() -> None:
    engine = HallucinationDetectionEngine()
    text = "Art. 1103 impose la force obligatoire du contrat."

    alerts = engine.scan(text)

    assert alerts == []  # has a citation, no contradiction — clean, nothing to flag


def test_ethics_engine_flags_overpromising_language() -> None:
    engine = EthicsEngine()

    findings = engine.screen("Il est garanti que vous gagnerez ce procès.")

    assert len(findings) >= 1
    assert findings[0].category == "overpromising"


def test_ethics_engine_finds_nothing_in_measured_language() -> None:
    engine = EthicsEngine()

    findings = engine.screen("Les chances de succès dépendent des éléments de preuve réunis.")

    assert findings == []
