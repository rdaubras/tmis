from tmis.ai_governance.compliance.schemas import ComplianceVerdict
from tmis.ai_governance.policy_engine.schemas import PolicyEvaluation
from tmis.ai_governance.risk_engine.schemas import RiskFinding, RiskSeverity

_BLOCKING_SEVERITIES = frozenset({RiskSeverity.HIGH, RiskSeverity.CRITICAL})


class ComplianceEngine:
    """The sprint's "COMPLIANCE" enforcement layer: combines a
    `PolicyEvaluation` (`ai_governance.policy_engine`) with the risks
    found by `ai_governance.risk_engine` into the single verdict that
    decides whether a production may be treated as final — "aucune
    réponse IA ne doit être considérée comme définitive sans respecter
    les politiques configurées par le cabinet" (sprint constraint).
    Distinct from `tmis.platform.compliance.ComplianceEngine`, which
    governs GDPR data-subject rights, not AI decision governance."""

    def check(
        self,
        production_id: str,
        policy_evaluation: PolicyEvaluation,
        risk_findings: list[RiskFinding],
    ) -> ComplianceVerdict:
        blocking_reasons: list[str] = list(
            policy_evaluation.reasons if not policy_evaluation.allowed else ()
        )
        warnings: list[str] = []

        for finding in risk_findings:
            if finding.severity in _BLOCKING_SEVERITIES:
                blocking_reasons.append(finding.explanation)
            else:
                warnings.append(finding.explanation)

        return ComplianceVerdict(
            production_id=production_id,
            compliant=not blocking_reasons,
            blocking_reasons=tuple(blocking_reasons),
            warnings=tuple(warnings),
        )
