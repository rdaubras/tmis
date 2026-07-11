from tmis.strategic_intelligence.simulation.schemas import (
    SimulationResult,
    SimulationScenario,
    new_simulation_id,
)


class SimulationEngine:
    """Read-only, keyword-matching simulation: flags which strategies'
    textual content references any of the hypothetical changes. Takes
    a plain `{strategy_id: searchable_text}` mapping rather than
    importing `strategy_engine.Strategy` — keeps this engine testable
    in isolation and guarantees it never mutates real strategy data,
    since it only ever reads copies of text it is handed."""

    def run(
        self,
        base_case_id: str,
        strategy_texts: dict[str, str],
        hypothetical_changes: tuple[str, ...],
    ) -> SimulationResult:
        scenario = SimulationScenario(
            id=new_simulation_id(),
            base_case_id=base_case_id,
            hypotheticals=hypothetical_changes,
        )
        affected: list[str] = []
        notes: list[str] = []
        for strategy_id, text in strategy_texts.items():
            lowered = text.lower()
            matches = [h for h in hypothetical_changes if h.lower() in lowered]
            if matches:
                affected.append(strategy_id)
                notes.append(
                    f"La stratégie {strategy_id} référence : {', '.join(matches)}."
                )
        return SimulationResult(
            scenario_id=scenario.id,
            affected_strategy_ids=tuple(affected),
            notes=tuple(notes),
        )
