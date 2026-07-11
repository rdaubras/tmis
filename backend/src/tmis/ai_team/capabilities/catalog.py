from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.capabilities.schemas import LegalDomain, TaskType

_SKILL_FOR_TASK_TYPE: dict[TaskType, str] = {
    TaskType.DOCUMENT_ANALYSIS: "document_analysis",
    TaskType.LEGAL_RESEARCH: "legal_research",
    TaskType.JURISPRUDENCE_RESEARCH: "jurisprudence_research",
    TaskType.RISK_ANALYSIS: "risk_analysis",
    TaskType.REASONING: "legal_reasoning",
    TaskType.DRAFTING: "drafting",
    TaskType.VERIFICATION: "verification",
    TaskType.QUALITY_CONTROL: "quality_control",
    TaskType.COORDINATION: "coordination",
    TaskType.CRITIQUE: "critique",
}

_DOMAIN_EXPERT_SKILL: dict[LegalDomain, str] = {
    LegalDomain.DATA_PROTECTION: "gdpr",
    LegalDomain.FISCAL: "tax_law",
    LegalDomain.SOCIAL: "social_law",
}

_DOMAIN_EXPERT_ROLE: dict[LegalDomain, AgentRole] = {
    LegalDomain.DATA_PROTECTION: AgentRole.GDPR_EXPERT,
    LegalDomain.FISCAL: AgentRole.TAX_EXPERT,
    LegalDomain.SOCIAL: AgentRole.SOCIAL_LAW_EXPERT,
}


def skill_for_task_type(task_type: TaskType) -> str:
    return _SKILL_FOR_TASK_TYPE[task_type]


def domain_expert_skill(domain: LegalDomain) -> str | None:
    """Returns the specialist skill a mission in `domain` additionally
    needs (e.g. a `data_protection` mission needs a `gdpr`-skilled
    agent), or `None` for domains with no dedicated expert role (see
    docs/54-guide-creation-equipe.md — équipes conditionnelles)."""
    return _DOMAIN_EXPERT_SKILL.get(domain)


def domain_expert_role(domain: LegalDomain) -> AgentRole | None:
    """Returns the `AgentRole` a mission in `domain` additionally
    needs, or `None` for domains with no dedicated expert — the single
    source of truth shared by `tmis.ai_team.teams` and
    `tmis.ai_team.planner` so the two never drift apart."""
    return _DOMAIN_EXPERT_ROLE.get(domain)
