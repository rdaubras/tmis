from tmis.strategic_intelligence.scenario_builder.schemas import Scenario, new_scenario_id

_DEFAULT_LIMITATION = (
    "Ce scénario est une exploration structurée, non une prédiction du "
    "résultat du procès."
)


class DefaultScenarioVariantBuilder:
    """Builds the three baseline variants — favorable, défavorable,
    intermédiaire — used whenever no specialized builder is registered."""

    name = "default"

    def build(
        self, base_case_id: str, context: str, hypotheses: tuple[str, ...]
    ) -> list[Scenario]:
        variants = (
            (
                "Scénario favorable",
                "Les hypothèses favorables se confirment et les éléments "
                "de preuve disponibles sont jugés suffisants.",
            ),
            (
                "Scénario défavorable",
                "Les contre-arguments prévalent et des éléments de preuve "
                "manquants s'avèrent déterminants.",
            ),
            (
                "Scénario intermédiaire",
                "Un accord partiel ou une décision mixte survient, "
                "combinant éléments favorables et défavorables.",
            ),
        )
        return [
            Scenario(
                id=new_scenario_id(),
                base_case_id=base_case_id,
                scenario_type=scenario_type,
                context=context,
                hypotheses=hypotheses,
                expected_impacts=(impact,),
                limitations=(_DEFAULT_LIMITATION,),
            )
            for scenario_type, impact in variants
        ]
