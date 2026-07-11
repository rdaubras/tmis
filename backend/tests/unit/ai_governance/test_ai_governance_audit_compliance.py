from tmis.ai_governance.audit.engine import AIAuditEngine
from tmis.ai_governance.audit.store import InMemoryAIAuditStore
from tmis.ai_governance.compliance.engine import ComplianceEngine
from tmis.ai_governance.policy_engine.schemas import PolicyEvaluation
from tmis.ai_governance.risk_engine.schemas import RiskCategory, RiskFinding, RiskSeverity

FIRM = "firm-a"
PRODUCTION = "prod-1"


def _audit_engine() -> AIAuditEngine:
    return AIAuditEngine(InMemoryAIAuditStore())


def test_record_captures_ai_specific_fields() -> None:
    engine = _audit_engine()

    entry = engine.record(
        FIRM,
        PRODUCTION,
        "user-1",
        "draft_generated",
        prompt="Rédige un avis",
        model_name="gpt-4-legal",
        cost_usd=0.02,
        duration_ms=1200,
    )

    assert entry.model_name == "gpt-4-legal"
    assert entry.cost_usd == 0.02


def test_list_for_firm_is_scoped() -> None:
    engine = _audit_engine()
    engine.record(FIRM, PRODUCTION, "user-1", "action")
    engine.record("other-firm", PRODUCTION, "user-1", "action")

    assert len(engine.list_for_firm(FIRM)) == 1


def test_list_for_production_is_scoped() -> None:
    engine = _audit_engine()
    engine.record(FIRM, "prod-a", "user-1", "action")
    engine.record(FIRM, "prod-b", "user-1", "action")

    assert len(engine.list_for_production(FIRM, "prod-a")) == 1


def test_export_csv_contains_a_header_and_one_row_per_entry() -> None:
    engine = _audit_engine()
    engine.record(FIRM, PRODUCTION, "user-1", "draft_generated", model_name="gpt-4-legal")

    csv_output = engine.export_csv(FIRM)

    lines = csv_output.strip().splitlines()
    assert len(lines) == 2
    assert "model_name" in lines[0]
    assert "gpt-4-legal" in lines[1]


def test_export_csv_for_firm_with_no_entries_has_only_a_header() -> None:
    engine = _audit_engine()

    csv_output = engine.export_csv(FIRM)

    assert len(csv_output.strip().splitlines()) == 1


def _allowed_evaluation() -> PolicyEvaluation:
    return PolicyEvaluation(
        id="polres-1", firm_id=FIRM, production_id=PRODUCTION, allowed=True, reasons=("ok",)
    )


def _blocked_evaluation() -> PolicyEvaluation:
    return PolicyEvaluation(
        id="polres-2",
        firm_id=FIRM,
        production_id=PRODUCTION,
        allowed=False,
        reasons=("confiance insuffisante",),
    )


def test_compliance_is_compliant_with_no_policy_failures_and_no_risks() -> None:
    engine = ComplianceEngine()

    verdict = engine.check(PRODUCTION, _allowed_evaluation(), [])

    assert verdict.compliant is True
    assert verdict.blocking_reasons == ()


def test_compliance_blocks_on_policy_failure() -> None:
    engine = ComplianceEngine()

    verdict = engine.check(PRODUCTION, _blocked_evaluation(), [])

    assert verdict.compliant is False
    assert "confiance insuffisante" in verdict.blocking_reasons


def test_compliance_blocks_on_high_or_critical_risk() -> None:
    engine = ComplianceEngine()
    risk = RiskFinding(
        id="risk-1",
        category=RiskCategory.MISSING_SOURCES,
        severity=RiskSeverity.HIGH,
        description="test",
        explanation="Risque critique détecté.",
    )

    verdict = engine.check(PRODUCTION, _allowed_evaluation(), [risk])

    assert verdict.compliant is False
    assert "Risque critique détecté." in verdict.blocking_reasons


def test_compliance_treats_low_and_medium_risk_as_warnings_only() -> None:
    engine = ComplianceEngine()
    risk = RiskFinding(
        id="risk-1",
        category=RiskCategory.OUTDATED_INFORMATION,
        severity=RiskSeverity.MEDIUM,
        description="test",
        explanation="Source un peu ancienne.",
    )

    verdict = engine.check(PRODUCTION, _allowed_evaluation(), [risk])

    assert verdict.compliant is True
    assert "Source un peu ancienne." in verdict.warnings
