from tmis.ai_governance.risk_engine.schemas import (
    RiskCategory,
    RiskFinding,
    RiskSeverity,
    new_risk_finding_id,
)

_OUTDATED_THRESHOLD_DAYS = 5 * 365
_LOW_CONFIDENCE_THRESHOLD = 0.5
_CRITICAL_CONFIDENCE_THRESHOLD = 0.3


class RiskEngine:
    """The sprint's "RISK ENGINE": identifies and classifies, by
    severity, the risks affecting one AI production. Deterministic and
    rule-based — every finding is explained, never a bare flag."""

    def assess(
        self,
        *,
        citation_count: int,
        contradiction_count: int,
        source_age_days: int | None,
        confidence_value: float,
        human_validated: bool,
    ) -> list[RiskFinding]:
        findings: list[RiskFinding] = []

        if citation_count == 0:
            findings.append(
                RiskFinding(
                    id=new_risk_finding_id(),
                    category=RiskCategory.MISSING_SOURCES,
                    severity=RiskSeverity.HIGH,
                    description="Aucune source ou citation identifiée",
                    explanation="La production ne référence aucune source documentaire ou "
                    "juridique — son affirmation la plus faible ne peut pas être vérifiée.",
                )
            )

        if contradiction_count > 0:
            severity = RiskSeverity.HIGH if contradiction_count >= 2 else RiskSeverity.MEDIUM
            findings.append(
                RiskFinding(
                    id=new_risk_finding_id(),
                    category=RiskCategory.CONTRADICTORY_SOURCES,
                    severity=severity,
                    description=(
                        f"{contradiction_count} contradiction(s) potentielle(s) détectée(s)"
                    ),
                    explanation="Des passages de sens opposé ont été détectés dans la même "
                    "production, ce qui peut indiquer des sources contradictoires.",
                )
            )

        if source_age_days is not None and source_age_days > _OUTDATED_THRESHOLD_DAYS:
            findings.append(
                RiskFinding(
                    id=new_risk_finding_id(),
                    category=RiskCategory.OUTDATED_INFORMATION,
                    severity=RiskSeverity.MEDIUM,
                    description=f"Source vieille de {source_age_days} jours",
                    explanation="La source la plus ancienne mobilisée dépasse le seuil de "
                    f"fraîcheur ({_OUTDATED_THRESHOLD_DAYS} jours) — une évolution législative "
                    "ou jurisprudentielle a pu intervenir depuis.",
                )
            )

        if confidence_value < _LOW_CONFIDENCE_THRESHOLD:
            severity = (
                RiskSeverity.CRITICAL
                if confidence_value < _CRITICAL_CONFIDENCE_THRESHOLD
                else RiskSeverity.HIGH
            )
            findings.append(
                RiskFinding(
                    id=new_risk_finding_id(),
                    category=RiskCategory.LOW_CONFIDENCE,
                    severity=severity,
                    description=f"Score de confiance faible ({confidence_value:.2f})",
                    explanation="Le score de confiance décomposé de la production est en "
                    f"dessous du seuil acceptable ({_LOW_CONFIDENCE_THRESHOLD:.2f}).",
                )
            )

        if not human_validated:
            findings.append(
                RiskFinding(
                    id=new_risk_finding_id(),
                    category=RiskCategory.NO_HUMAN_VALIDATION,
                    severity=RiskSeverity.MEDIUM,
                    description="Aucune validation humaine enregistrée",
                    explanation="Cette production n'a pas encore été relue ni validée par un "
                    "utilisateur humain.",
                )
            )

        return findings
