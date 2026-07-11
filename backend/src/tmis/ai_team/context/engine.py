from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.context.schemas import ContextSlice, ContextTraceEntry

_CHARS_PER_TOKEN = 4

_RELEVANT_KEY_PREFIXES: dict[AgentRole, frozenset[str]] = {
    AgentRole.DOCUMENT_ANALYST: frozenset({"case_"}),
    AgentRole.LEGAL_RESEARCHER: frozenset({"case_", "document_analysis_"}),
    AgentRole.JURISPRUDENCE_EXPERT: frozenset({"case_", "legal_research_"}),
    AgentRole.GDPR_EXPERT: frozenset({"case_", "document_analysis_", "legal_research_"}),
    AgentRole.TAX_EXPERT: frozenset({"case_", "document_analysis_", "legal_research_"}),
    AgentRole.SOCIAL_LAW_EXPERT: frozenset({"case_", "document_analysis_", "legal_research_"}),
    AgentRole.DRAFTER: frozenset(
        {
            "case_",
            "document_analysis_",
            "legal_research_",
            "jurisprudence_research_",
            "risk_analysis_",
        }
    ),
    AgentRole.VERIFIER: frozenset({"case_", "drafting_", "reasoning_"}),
    AgentRole.QUALITY_CONTROLLER: frozenset(),  # empty prefix set means "everything" (see below)
    AgentRole.CRITIC: frozenset(),
}


def _estimate_tokens(value: object) -> int:
    return max(1, len(str(value)) // _CHARS_PER_TOKEN)


class ContextEngine:
    """Builds a per-agent slice of the shared mission context, limiting
    token consumption and keeping a full trace of what was transmitted
    to whom (see docs/56-guide-consensus-critique.md — Context Engine).
    A role absent from the relevance table, or mapped to an empty
    prefix set (`QUALITY_CONTROLLER`, `CRITIC`), receives the full
    context by design — both roles exist specifically to review
    everything produced so far."""

    def __init__(self) -> None:
        self._trace: list[ContextTraceEntry] = []

    def build_context_for(
        self, mission_id: str, agent_role: AgentRole, mission_context: dict[str, object]
    ) -> ContextSlice:
        prefixes = _RELEVANT_KEY_PREFIXES.get(agent_role)
        if not prefixes:
            relevant = dict(mission_context)
        else:
            relevant = {
                key: value
                for key, value in mission_context.items()
                if any(key.startswith(prefix) for prefix in prefixes)
            }

        token_estimate = sum(_estimate_tokens(value) for value in relevant.values())
        self._trace.append(
            ContextTraceEntry(
                mission_id=mission_id,
                agent_role=agent_role,
                keys_included=tuple(sorted(relevant)),
                token_estimate=token_estimate,
            )
        )
        return ContextSlice(agent_role=agent_role, content=relevant, token_estimate=token_estimate)

    def trace_for_mission(self, mission_id: str) -> list[ContextTraceEntry]:
        return [entry for entry in self._trace if entry.mission_id == mission_id]
