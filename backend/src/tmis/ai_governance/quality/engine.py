from tmis.ai_governance.quality.schemas import GovernanceQualityBreakdown


class GovernanceQualityEngine:
    """Composes the five factors above into one overall governance
    quality figure for a production. Takes pre-computed factor values,
    same decoupled-input convention as `ai_governance.confidence`, so
    this module never imports `explainability`/`provenance`/
    `risk_engine`/`human_validation` directly."""

    def evaluate(
        self,
        production_id: str,
        *,
        explainability_completeness: float,
        provenance_completeness: float,
        confidence_value: float,
        risk_absence: float,
        human_validation_coverage: float,
    ) -> GovernanceQualityBreakdown:
        return GovernanceQualityBreakdown(
            production_id=production_id,
            explainability_completeness=explainability_completeness,
            provenance_completeness=provenance_completeness,
            confidence_value=confidence_value,
            risk_absence=risk_absence,
            human_validation_coverage=human_validation_coverage,
        )
