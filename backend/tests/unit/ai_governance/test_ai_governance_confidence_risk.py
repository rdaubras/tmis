from tmis.ai_governance.confidence.engine import GovernanceConfidenceEngine
from tmis.ai_governance.confidence.schemas import GovernanceConfidenceWeights
from tmis.ai_governance.risk_engine.engine import RiskEngine
from tmis.ai_governance.risk_engine.schemas import RiskCategory, RiskSeverity


def test_confidence_engine_decomposes_the_five_sprint_factors() -> None:
    engine = GovernanceConfidenceEngine()

    score = engine.score(
        "prod-1",
        source_quality=0.8,
        reasoning_coherence=0.9,
        human_validation=0.0,
        multi_agent_consensus=0.7,
        model_stability=0.85,
    )

    assert set(score.factors) == {
        "source_quality",
        "reasoning_coherence",
        "human_validation",
        "multi_agent_consensus",
        "model_stability",
    }
    assert 0.0 <= score.value <= 1.0
    assert score.explanation


def test_confidence_engine_perfect_factors_yield_a_perfect_score() -> None:
    engine = GovernanceConfidenceEngine()

    score = engine.score(
        "prod-1",
        source_quality=1.0,
        reasoning_coherence=1.0,
        human_validation=1.0,
        multi_agent_consensus=1.0,
        model_stability=1.0,
    )

    assert score.value == 1.0


def test_confidence_engine_respects_custom_weights() -> None:
    engine = GovernanceConfidenceEngine()
    weights = GovernanceConfidenceWeights(
        source_quality=1.0,
        reasoning_coherence=0.0,
        human_validation=0.0,
        multi_agent_consensus=0.0,
        model_stability=0.0,
    )

    score = engine.score(
        "prod-1",
        source_quality=0.5,
        reasoning_coherence=0.0,
        human_validation=0.0,
        multi_agent_consensus=0.0,
        model_stability=0.0,
        weights=weights,
    )

    assert score.value == 0.5


def test_confidence_weights_normalize_when_all_zero() -> None:
    weights = GovernanceConfidenceWeights(0, 0, 0, 0, 0)

    normalized = weights.normalized()

    assert sum(
        [
            normalized.source_quality,
            normalized.reasoning_coherence,
            normalized.human_validation,
            normalized.multi_agent_consensus,
            normalized.model_stability,
        ]
    ) == 1.0


def test_risk_engine_flags_missing_sources() -> None:
    engine = RiskEngine()

    findings = engine.assess(
        citation_count=0,
        contradiction_count=0,
        source_age_days=None,
        confidence_value=0.9,
        human_validated=True,
    )

    assert any(f.category is RiskCategory.MISSING_SOURCES for f in findings)


def test_risk_engine_flags_contradictions_with_escalating_severity() -> None:
    engine = RiskEngine()

    single = engine.assess(
        citation_count=1,
        contradiction_count=1,
        source_age_days=None,
        confidence_value=0.9,
        human_validated=True,
    )
    multiple = engine.assess(
        citation_count=1,
        contradiction_count=3,
        source_age_days=None,
        confidence_value=0.9,
        human_validated=True,
    )

    single_finding = next(f for f in single if f.category is RiskCategory.CONTRADICTORY_SOURCES)
    multiple_finding = next(
        f for f in multiple if f.category is RiskCategory.CONTRADICTORY_SOURCES
    )
    assert single_finding.severity is RiskSeverity.MEDIUM
    assert multiple_finding.severity is RiskSeverity.HIGH


def test_risk_engine_flags_outdated_sources() -> None:
    engine = RiskEngine()

    findings = engine.assess(
        citation_count=1,
        contradiction_count=0,
        source_age_days=3000,
        confidence_value=0.9,
        human_validated=True,
    )

    assert any(f.category is RiskCategory.OUTDATED_INFORMATION for f in findings)


def test_risk_engine_low_confidence_becomes_critical_below_threshold() -> None:
    engine = RiskEngine()

    findings = engine.assess(
        citation_count=1,
        contradiction_count=0,
        source_age_days=None,
        confidence_value=0.2,
        human_validated=True,
    )

    finding = next(f for f in findings if f.category is RiskCategory.LOW_CONFIDENCE)
    assert finding.severity is RiskSeverity.CRITICAL


def test_risk_engine_flags_absence_of_human_validation() -> None:
    engine = RiskEngine()

    findings = engine.assess(
        citation_count=1,
        contradiction_count=0,
        source_age_days=None,
        confidence_value=0.9,
        human_validated=False,
    )

    assert any(f.category is RiskCategory.NO_HUMAN_VALIDATION for f in findings)


def test_risk_engine_returns_no_findings_for_a_clean_production() -> None:
    engine = RiskEngine()

    findings = engine.assess(
        citation_count=2,
        contradiction_count=0,
        source_age_days=100,
        confidence_value=0.95,
        human_validated=True,
    )

    assert findings == []


def test_every_risk_finding_has_a_non_empty_explanation() -> None:
    engine = RiskEngine()

    findings = engine.assess(
        citation_count=0,
        contradiction_count=2,
        source_age_days=3000,
        confidence_value=0.1,
        human_validated=False,
    )

    assert len(findings) == 5
    assert all(f.explanation for f in findings)
