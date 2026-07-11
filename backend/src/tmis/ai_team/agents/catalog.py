from dataclasses import dataclass

from tmis.ai_team.agents.ports import KernelPort, TeamAgentPort
from tmis.ai_team.agents.prompted_agent import PromptedTeamAgent
from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.registry.schemas import AgentDescriptor


@dataclass(frozen=True, slots=True)
class _RoleDefinition:
    agent_id: str
    name: str
    role: AgentRole
    description: str
    system_prompt: str
    skills: frozenset[str]
    estimated_cost_usd: float = 0.01
    average_duration_seconds: float = 5.0
    quality_score: float = 0.8


_ROLE_DEFINITIONS: tuple[_RoleDefinition, ...] = (
    _RoleDefinition(
        agent_id="agent-document-analyst",
        name="Analyste documentaire",
        role=AgentRole.DOCUMENT_ANALYST,
        description="Analyse les documents du dossier et en extrait les faits saillants.",
        system_prompt=(
            "Tu es un analyste documentaire juridique. Résume les points factuels "
            "essentiels du dossier, sans conclusion juridique."
        ),
        skills=frozenset({"document_analysis"}),
    ),
    _RoleDefinition(
        agent_id="agent-legal-researcher",
        name="Chercheur juridique",
        role=AgentRole.LEGAL_RESEARCHER,
        description="Recherche les textes et sources juridiques applicables.",
        system_prompt=(
            "Tu es un chercheur juridique. Identifie les textes de loi et sources "
            "applicables au dossier, avec leurs références précises."
        ),
        skills=frozenset({"legal_research"}),
    ),
    _RoleDefinition(
        agent_id="agent-jurisprudence-expert",
        name="Expert en jurisprudence",
        role=AgentRole.JURISPRUDENCE_EXPERT,
        description="Recherche et compare la jurisprudence pertinente.",
        system_prompt=(
            "Tu es un expert en jurisprudence. Identifie les décisions pertinentes "
            "et compare les solutions retenues par les juridictions."
        ),
        skills=frozenset({"jurisprudence_research"}),
    ),
    _RoleDefinition(
        agent_id="agent-drafter",
        name="Rédacteur",
        role=AgentRole.DRAFTER,
        description="Rédige un brouillon de document à partir du raisonnement établi.",
        system_prompt=(
            "Tu es un rédacteur juridique. Rédige un brouillon structuré à partir "
            "des éléments d'analyse fournis. Précise systématiquement qu'il s'agit "
            "d'un brouillon à valider."
        ),
        skills=frozenset({"drafting"}),
    ),
    _RoleDefinition(
        agent_id="agent-verifier",
        name="Vérificateur",
        role=AgentRole.VERIFIER,
        description="Vérifie la fiabilité et la cohérence des productions.",
        system_prompt=(
            "Tu es un vérificateur. Contrôle la cohérence et la fiabilité du contenu "
            "fourni et signale toute affirmation non étayée."
        ),
        skills=frozenset({"verification"}),
    ),
    _RoleDefinition(
        agent_id="agent-quality-controller",
        name="Contrôleur qualité",
        role=AgentRole.QUALITY_CONTROLLER,
        description="Contrôle la qualité finale avant remise du livrable.",
        system_prompt=(
            "Tu es un contrôleur qualité. Vérifie la complétude et la clarté du "
            "livrable avant sa remise, et liste les points restant à améliorer."
        ),
        skills=frozenset({"quality_control"}),
    ),
    _RoleDefinition(
        agent_id="agent-gdpr-expert",
        name="Expert RGPD",
        role=AgentRole.GDPR_EXPERT,
        description="Analyse les enjeux de protection des données personnelles.",
        system_prompt=(
            "Tu es un expert RGPD. Identifie les enjeux de protection des données "
            "personnelles et les risques de non-conformité."
        ),
        skills=frozenset({"gdpr", "risk_analysis"}),
    ),
    _RoleDefinition(
        agent_id="agent-tax-expert",
        name="Expert fiscal",
        role=AgentRole.TAX_EXPERT,
        description="Analyse les enjeux fiscaux du dossier.",
        system_prompt="Tu es un expert fiscal. Identifie les enjeux et risques fiscaux du dossier.",
        skills=frozenset({"tax_law", "risk_analysis"}),
    ),
    _RoleDefinition(
        agent_id="agent-social-law-expert",
        name="Expert social",
        role=AgentRole.SOCIAL_LAW_EXPERT,
        description="Analyse les enjeux de droit social du dossier.",
        system_prompt=(
            "Tu es un expert en droit social. Identifie les enjeux et risques de "
            "droit du travail et de la sécurité sociale du dossier."
        ),
        skills=frozenset({"social_law", "risk_analysis"}),
    ),
    _RoleDefinition(
        agent_id="agent-critic",
        name="Agent critique",
        role=AgentRole.CRITIC,
        description="Critique les productions des autres agents.",
        system_prompt=(
            "Tu es un agent critique. Recherche les incohérences, vérifie les "
            "références citées, détecte les oublis, et propose des améliorations."
        ),
        skills=frozenset({"critique"}),
    ),
)


def build_default_agents(kernel: KernelPort) -> dict[str, TeamAgentPort]:
    """Builds one `PromptedTeamAgent` per default role definition,
    keyed by agent id — the runtime counterpart of
    `default_descriptors()`."""
    return {
        definition.agent_id: PromptedTeamAgent(
            definition.name, definition.role, definition.system_prompt, kernel
        )
        for definition in _ROLE_DEFINITIONS
    }


def default_descriptors() -> list[AgentDescriptor]:
    """Builds the `AgentDescriptor` catalog entry for every default
    role definition — what the registry lists, independent of whether
    a runtime instance has been constructed."""
    return [
        AgentDescriptor(
            id=definition.agent_id,
            name=definition.name,
            role=definition.role,
            description=definition.description,
            skills=definition.skills,
            estimated_cost_usd=definition.estimated_cost_usd,
            average_duration_seconds=definition.average_duration_seconds,
            quality_score=definition.quality_score,
        )
        for definition in _ROLE_DEFINITIONS
    ]
