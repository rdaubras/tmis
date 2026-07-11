from enum import Enum


class AgentRole(str, Enum):
    """The specialized roles an AI Team member can hold (see
    docs/53-guide-creation-agent.md). `COORDINATOR` is special: it
    never performs analysis itself (see `tmis.ai_team.coordinator`)."""

    COORDINATOR = "coordinator"
    DOCUMENT_ANALYST = "document_analyst"
    LEGAL_RESEARCHER = "legal_researcher"
    JURISPRUDENCE_EXPERT = "jurisprudence_expert"
    DRAFTER = "drafter"
    VERIFIER = "verifier"
    QUALITY_CONTROLLER = "quality_controller"
    GDPR_EXPERT = "gdpr_expert"
    TAX_EXPERT = "tax_expert"
    SOCIAL_LAW_EXPERT = "social_law_expert"
    CRITIC = "critic"
