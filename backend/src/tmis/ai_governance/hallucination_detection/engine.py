from tmis.ai_fabric.evaluation.engine import ResponseEvaluator
from tmis.ai_governance.hallucination_detection.schemas import (
    HallucinationAlert,
    new_hallucination_alert_id,
)

_EXCERPT_LENGTH = 200


class HallucinationDetectionEngine:
    """The sprint's "HALLUCINATION DETECTION": signals insufficiently
    supported claims — never deletes content, only alerts and
    recommends. Built directly on
    `tmis.ai_fabric.evaluation.ResponseEvaluator` (Sprint 14) rather
    than reimplementing citation counting or contradiction detection
    a third time in the codebase."""

    def __init__(self, evaluator: ResponseEvaluator | None = None) -> None:
        self._evaluator = evaluator or ResponseEvaluator()

    def scan(self, text: str) -> list[HallucinationAlert]:
        metrics = self._evaluator.evaluate(text)
        alerts: list[HallucinationAlert] = []

        if metrics.length_words > 0 and metrics.citation_count == 0:
            alerts.append(
                HallucinationAlert(
                    id=new_hallucination_alert_id(),
                    excerpt=text[:_EXCERPT_LENGTH],
                    reason="Aucune citation ni référence identifiée pour étayer cette production.",
                    recommendation="Ajouter une source documentaire, une jurisprudence ou un "
                    "article de loi à l'appui avant tout export.",
                )
            )

        for flag in metrics.contradiction_flags:
            alerts.append(
                HallucinationAlert(
                    id=new_hallucination_alert_id(),
                    excerpt=flag,
                    reason="Contradiction interne détectée — signe possible d'une affirmation "
                    "non vérifiée.",
                    recommendation="Vérifier manuellement les deux passages en conflit avant "
                    "toute validation humaine.",
                )
            )

        return alerts
