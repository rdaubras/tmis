from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.capabilities.schemas import TaskType

MissionStep = tuple[TaskType, AgentRole]

MISSION_TEMPLATES: dict[str, tuple[MissionStep, ...]] = {
    "quick_review": (
        (TaskType.VERIFICATION, AgentRole.VERIFIER),
        (TaskType.QUALITY_CONTROL, AgentRole.QUALITY_CONTROLLER),
    ),
    "drafting_only": (
        (TaskType.DRAFTING, AgentRole.DRAFTER),
        (TaskType.VERIFICATION, AgentRole.VERIFIER),
    ),
    "standard_analysis": (
        (TaskType.DOCUMENT_ANALYSIS, AgentRole.DOCUMENT_ANALYST),
        (TaskType.LEGAL_RESEARCH, AgentRole.LEGAL_RESEARCHER),
        (TaskType.VERIFICATION, AgentRole.VERIFIER),
        (TaskType.QUALITY_CONTROL, AgentRole.QUALITY_CONTROLLER),
    ),
    "full_case_analysis": (
        (TaskType.DOCUMENT_ANALYSIS, AgentRole.DOCUMENT_ANALYST),
        (TaskType.LEGAL_RESEARCH, AgentRole.LEGAL_RESEARCHER),
        (TaskType.JURISPRUDENCE_RESEARCH, AgentRole.JURISPRUDENCE_EXPERT),
        (TaskType.REASONING, AgentRole.DRAFTER),
        (TaskType.DRAFTING, AgentRole.DRAFTER),
        (TaskType.VERIFICATION, AgentRole.VERIFIER),
        (TaskType.QUALITY_CONTROL, AgentRole.QUALITY_CONTROLLER),
    ),
}

DEFAULT_MISSION_TEMPLATE = "full_case_analysis"


def template_for(case_type: str) -> tuple[MissionStep, ...]:
    return MISSION_TEMPLATES.get(case_type, MISSION_TEMPLATES[DEFAULT_MISSION_TEMPLATE])


def roles_for_case_type(case_type: str) -> tuple[AgentRole, ...]:
    """The distinct roles a case-type template needs, in first-seen
    order — the single source of truth both `TeamBuilder` (which
    agents to include) and `Planner` (which agent each sub-task is
    assigned to) read from, so a team can never be composed without an
    agent for a role the plan actually requires (see
    docs/54-guide-creation-equipe.md)."""
    seen: list[AgentRole] = []
    for _task_type, role in template_for(case_type):
        if role not in seen:
            seen.append(role)
    return tuple(seen)
