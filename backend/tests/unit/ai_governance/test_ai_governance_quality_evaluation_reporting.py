from tmis.ai_governance.evaluation.engine import GovernanceEvaluator
from tmis.ai_governance.evaluation.schemas import GovernanceRunMetrics
from tmis.ai_governance.evaluation.store import InMemoryGovernanceMetricsSink
from tmis.ai_governance.explainability.schemas import ExplainabilityReport
from tmis.ai_governance.quality.engine import GovernanceQualityEngine
from tmis.ai_governance.reporting.engine import ReportGenerator
from tmis.ai_governance.reporting.schemas import ReportType

PRODUCTION = "prod-1"
FIRM = "firm-a"


def test_quality_engine_averages_the_five_factors() -> None:
    engine = GovernanceQualityEngine()

    breakdown = engine.evaluate(
        PRODUCTION,
        explainability_completeness=1.0,
        provenance_completeness=1.0,
        confidence_value=1.0,
        risk_absence=1.0,
        human_validation_coverage=1.0,
    )

    assert breakdown.overall == 1.0


def test_quality_engine_overall_reflects_a_mixed_score() -> None:
    engine = GovernanceQualityEngine()

    breakdown = engine.evaluate(
        PRODUCTION,
        explainability_completeness=1.0,
        provenance_completeness=0.0,
        confidence_value=1.0,
        risk_absence=0.0,
        human_validation_coverage=1.0,
    )

    assert breakdown.overall == 0.6


def test_governance_evaluator_fans_out_to_every_sink() -> None:
    sink_a = InMemoryGovernanceMetricsSink()
    sink_b = InMemoryGovernanceMetricsSink()
    evaluator = GovernanceEvaluator([sink_a, sink_b])
    metrics = GovernanceRunMetrics(
        production_id=PRODUCTION, duration_ms=120.0, risk_count=1, finding_count=2
    )

    evaluator.record(metrics)

    assert sink_a.all() == [metrics]
    assert sink_b.all() == [metrics]


def test_governance_evaluator_with_no_sinks_does_not_raise() -> None:
    evaluator = GovernanceEvaluator()

    evaluator.record(
        GovernanceRunMetrics(
            production_id=PRODUCTION, duration_ms=1.0, risk_count=0, finding_count=0
        )
    )


def test_report_generator_builds_an_explainability_report() -> None:
    generator = ReportGenerator()
    report = ExplainabilityReport(
        id="expl-1",
        firm_id=FIRM,
        production_id=PRODUCTION,
        summary="Le bail peut être résilié.",
        steps_followed=("Question", "Analyse"),
        agents_involved=(),
        models_used=(),
        legal_references=("Code civil art. 1103",),
        documents_consulted=(),
    )

    result = generator.generate(ReportType.EXPLAINABILITY, FIRM, PRODUCTION, report=report)

    assert result.title == "Rapport d'explicabilité"
    assert any(s.title == "Résumé" and s.content == report.summary for s in result.sections)


def test_report_generator_raises_for_unregistered_type() -> None:
    generator = ReportGenerator()

    class _FakeType:
        value = "fake"

    try:
        generator.generate(_FakeType(), FIRM, PRODUCTION)  # type: ignore[arg-type]
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_report_generator_is_extensible_via_register() -> None:
    from tmis.ai_governance.reporting.schemas import GovernanceReport, ReportSection

    generator = ReportGenerator()

    def _custom_builder(firm_id: str, production_id: str | None, **_: object) -> GovernanceReport:
        return GovernanceReport(
            id="custom-1",
            type=ReportType.QUALITY,
            firm_id=firm_id,
            production_id=production_id,
            title="Rapport personnalisé",
            sections=(ReportSection("Test", "contenu"),),
        )

    generator.register(ReportType.QUALITY, _custom_builder)
    result = generator.generate(ReportType.QUALITY, FIRM, PRODUCTION)

    assert result.title == "Rapport personnalisé"
