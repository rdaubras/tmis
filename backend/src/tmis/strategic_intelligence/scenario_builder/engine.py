from tmis.strategic_intelligence.scenario_builder.builders import DefaultScenarioVariantBuilder
from tmis.strategic_intelligence.scenario_builder.ports import ScenarioVariantBuilderPort
from tmis.strategic_intelligence.scenario_builder.schemas import Scenario


class ScenarioBuilderEngine:
    """Runs every registered `ScenarioVariantBuilderPort` over a base
    case and collects their scenarios. Seeded with
    `DefaultScenarioVariantBuilder`; `register()` adds a new variant
    family at runtime without modifying this class."""

    def __init__(self, builders: list[ScenarioVariantBuilderPort] | None = None) -> None:
        self._builders: list[ScenarioVariantBuilderPort] = (
            list(builders) if builders is not None else [DefaultScenarioVariantBuilder()]
        )

    def register(self, builder: ScenarioVariantBuilderPort) -> None:
        self._builders.append(builder)

    def build_scenarios(
        self, base_case_id: str, context: str, hypotheses: tuple[str, ...] = ()
    ) -> list[Scenario]:
        scenarios: list[Scenario] = []
        for builder in self._builders:
            scenarios.extend(builder.build(base_case_id, context, hypotheses))
        return scenarios
