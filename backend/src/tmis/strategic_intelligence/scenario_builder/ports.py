from typing import Protocol

from tmis.strategic_intelligence.scenario_builder.schemas import Scenario


class ScenarioVariantBuilderPort(Protocol):
    """One pluggable scenario-variant builder. `ScenarioBuilderEngine` is
    closed over this narrow contract so a new variant family (e.g.
    "scénario réglementaire") can be registered without touching the
    engine — same extensibility pattern as
    `ai_governance.bias_detection.BiasDetectorPort`."""

    name: str

    def build(
        self, base_case_id: str, context: str, hypotheses: tuple[str, ...]
    ) -> list[Scenario]: ...
