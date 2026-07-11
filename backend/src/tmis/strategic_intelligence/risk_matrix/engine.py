from tmis.strategic_intelligence.risk_matrix.schemas import (
    DEFAULT_CRITERIA,
    RiskCriterion,
    RiskMatrixResult,
)


class RiskMatrixEngine:
    """Combines pre-computed strategy factors into a single risk score,
    always with a human-readable `explanation`. Takes factor values as
    parameters rather than deriving them itself — same decoupled-input
    convention as `ai_governance.confidence.GovernanceConfidenceEngine`,
    keeping this engine testable without mocking `strategy_engine`."""

    def evaluate(
        self,
        strategy_id: str,
        *,
        documentary_solidity: float,
        reasoning_coherence: float,
        evidence_dependency: float,
        uncertainty: float,
        requires_human_validation: bool,
        criteria: tuple[RiskCriterion, ...] | None = None,
    ) -> RiskMatrixResult:
        weights = {c.name: c.weight for c in (criteria or DEFAULT_CRITERIA)}
        total_weight = sum(weights.values()) or 1.0

        factors = {
            "documentary_solidity": 1.0 - documentary_solidity,
            "reasoning_coherence": 1.0 - reasoning_coherence,
            "evidence_dependency": evidence_dependency,
            "uncertainty": uncertainty,
            "requires_human_validation": 1.0 if requires_human_validation else 0.0,
        }

        score = (
            sum(weights.get(name, 0.0) * value for name, value in factors.items())
            / total_weight
        )
        score = round(max(0.0, min(1.0, score)), 2)

        explanation = (
            f"solidité documentaire {documentary_solidity:.2f}, cohérence du "
            f"raisonnement {reasoning_coherence:.2f}, dépendance aux preuves "
            f"{evidence_dependency:.2f}, incertitude {uncertainty:.2f}, "
            f"validation humaine requise : {requires_human_validation}."
        )

        return RiskMatrixResult(
            strategy_id=strategy_id,
            score=score,
            explanation=explanation,
            factors=factors,
        )
