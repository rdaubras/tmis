from enum import Enum


class LegalDomain(str, Enum):
    """Legal domains a mission can touch (see docs/54-guide-creation-equipe.md).
    Open-ended in spirit (a new domain is a new enum member, not a new
    module) — kept as an enum rather than a free string so the Team
    Builder and Planner can match on it exhaustively."""

    GENERAL = "general"
    CIVIL = "civil"
    COMMERCIAL = "commercial"
    SOCIAL = "social"
    FISCAL = "fiscal"
    DATA_PROTECTION = "data_protection"
    PENAL = "penal"


class TaskType(str, Enum):
    """The pipeline stages a `Planner` decomposes a request into (see
    docs/53-guide-creation-agent.md)."""

    DOCUMENT_ANALYSIS = "document_analysis"
    LEGAL_RESEARCH = "legal_research"
    JURISPRUDENCE_RESEARCH = "jurisprudence_research"
    RISK_ANALYSIS = "risk_analysis"
    REASONING = "reasoning"
    DRAFTING = "drafting"
    VERIFICATION = "verification"
    QUALITY_CONTROL = "quality_control"
    COORDINATION = "coordination"
    CRITIQUE = "critique"
