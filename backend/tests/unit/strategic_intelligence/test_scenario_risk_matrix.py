from tmis.strategic_intelligence.risk_matrix.engine import RiskMatrixEngine
from tmis.strategic_intelligence.risk_matrix.schemas import RiskCriterion
from tmis.strategic_intelligence.scenario_builder.engine import ScenarioBuilderEngine
from tmis.strategic_intelligence.scenario_builder.ports import ScenarioVariantBuilderPort
from tmis.strategic_intelligence.scenario_builder.schemas import Scenario, new_scenario_id


def test_scenario_builder_default_yields_three_variants() -> None:
    engine = ScenarioBuilderEngine()

    scenarios = engine.build_scenarios("case-1", "Licenciement contesté")

    assert len(scenarios) == 3
    assert {s.scenario_type for s in scenarios} == {
        "Scénario favorable",
        "Scénario défavorable",
        "Scénario intermédiaire",
    }


def test_scenario_builder_every_scenario_carries_a_limitation() -> None:
    engine = ScenarioBuilderEngine()

    scenarios = engine.build_scenarios("case-1", "context")

    for scenario in scenarios:
        assert scenario.limitations


class _StubVariantBuilder:
    name = "réglementaire"

    def build(
        self, base_case_id: str, context: str, hypotheses: tuple[str, ...]
    ) -> list[Scenario]:
        return [
            Scenario(
                id=new_scenario_id(),
                base_case_id=base_case_id,
                scenario_type="Scénario réglementaire",
                context=context,
                limitations=("test",),
            )
        ]


def test_scenario_builder_register_extends_without_modifying_engine() -> None:
    engine = ScenarioBuilderEngine()
    builder: ScenarioVariantBuilderPort = _StubVariantBuilder()
    engine.register(builder)

    scenarios = engine.build_scenarios("case-1", "context")

    assert len(scenarios) == 4
    assert any(s.scenario_type == "Scénario réglementaire" for s in scenarios)


def test_risk_matrix_returns_score_between_zero_and_one() -> None:
    engine = RiskMatrixEngine()

    result = engine.evaluate(
        "strategy-1",
        documentary_solidity=0.7,
        reasoning_coherence=0.8,
        evidence_dependency=0.4,
        uncertainty=0.3,
        requires_human_validation=True,
    )

    assert 0.0 <= result.score <= 1.0
    assert result.explanation
    assert set(result.factors) == {
        "documentary_solidity",
        "reasoning_coherence",
        "evidence_dependency",
        "uncertainty",
        "requires_human_validation",
    }


def test_risk_matrix_weak_documentary_solidity_raises_risk() -> None:
    engine = RiskMatrixEngine()

    strong = engine.evaluate(
        "strategy-1",
        documentary_solidity=0.9,
        reasoning_coherence=0.9,
        evidence_dependency=0.1,
        uncertainty=0.1,
        requires_human_validation=False,
    )
    weak = engine.evaluate(
        "strategy-1",
        documentary_solidity=0.1,
        reasoning_coherence=0.9,
        evidence_dependency=0.1,
        uncertainty=0.1,
        requires_human_validation=False,
    )

    assert weak.score > strong.score


def test_risk_matrix_accepts_custom_criteria() -> None:
    engine = RiskMatrixEngine()
    criteria = (RiskCriterion("documentary_solidity", 1.0),)

    result = engine.evaluate(
        "strategy-1",
        documentary_solidity=0.0,
        reasoning_coherence=1.0,
        evidence_dependency=0.0,
        uncertainty=0.0,
        requires_human_validation=False,
        criteria=criteria,
    )

    assert result.score == 1.0
