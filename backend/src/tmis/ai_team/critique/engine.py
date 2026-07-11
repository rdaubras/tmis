from tmis.ai.schemas.agent import AgentOutput, ConfidenceLevel
from tmis.ai_team.critique.schemas import Critique

_MIN_RESULT_LENGTH = 20


class CritiqueEngine:
    """Rule-based critique of an `AgentOutput` (see
    docs/57-guide-critique.md — Critique Engine): searches for
    incoherence, missing references, and omissions without itself
    calling a model — the model-backed complement is the `CRITIC`
    role in the default agent catalog (`AgentRole.CRITIC`), which a
    mission can include in its plan for a richer, LLM-produced
    critique. This engine is the deterministic baseline every
    production is checked against regardless of whether a critic
    agent ran."""

    def critique(self, sub_task_id: str, agent_id: str, output: AgentOutput) -> Critique:
        issues: list[str] = []
        suggestions: list[str] = []

        text = str(output.result.get("text", ""))
        if len(text.strip()) < _MIN_RESULT_LENGTH:
            issues.append("La production semble incomplète (contenu très court).")

        if output.confidence is ConfidenceLevel.LOW and not output.warnings:
            issues.append("Confiance faible déclarée sans avertissement associé.")

        if not output.citations:
            suggestions.append("Ajouter des références ou citations à l'appui.")

        if not output.warnings:
            suggestions.append("Confirmer qu'aucune réserve ou incertitude n'a été omise.")

        return Critique(
            target_sub_task_id=sub_task_id,
            target_agent_id=agent_id,
            issues=tuple(issues),
            suggestions=tuple(suggestions),
        )
