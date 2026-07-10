from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StrategyOption:
    """One possible analytical path for a hypothesis — never a
    recommendation: `StrategyEngine` always returns every option it
    finds, the avocat decides which (if any) to pursue (see
    docs/25-legal-reasoning.md — Strategy Engine)."""

    id: str
    hypothesis_id: str
    objective: str
    favorable_points: tuple[str, ...]
    risks: tuple[str, ...]
    missing_elements: tuple[str, ...]
