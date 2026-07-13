from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.cabinet_knowledge.knowledge.schemas import KnowledgeType
from tmis.legal_copilot_framework.copilot.schemas import LegalCopilot
from tmis.legal_copilot_framework.copilots.deps import DemoCopilotDeps
from tmis.legal_copilot_framework.reasoning_packs.schemas import ReasoningStrategyType
from tmis.legal_copilot_framework.sdk.schemas import CopilotSpec
from tmis.legal_copilot_framework.validation_policies.schemas import CopilotValidationPolicyType
from tmis.legal_drafting.templates.schemas import DocumentType
from tmis.platform_sdk.permissions.schemas import ExtensionPermission

_FIRM_KNOWLEDGE_AUTHOR = "sprint24-demo-seed"


def build(deps: DemoCopilotDeps) -> LegalCopilot:
    """MVP copilot for contentieux civil et commercial: qualification
    des faits, argumentation contradictoire, rédaction des actes de
    procédure. Demonstrates the pack architecture end to end — not a
    full contentieux business-logic implementation (Sprint 24 Phase
    12 scope)."""

    deps.prompt_registry.register(
        "contentieux-system",
        category="system",
        template=(
            "Tu es le copilote Contentieux du cabinet {cabinet}. Analyse le dossier "
            "{dossier}, qualifie juridiquement les faits et identifie les risques."
        ),
        variables=("cabinet", "dossier"),
    )
    prompt_pack = deps.prompt_packs.register_pack(
        "pp-contentieux",
        "Prompts Contentieux",
        LegalDomain.CIVIL,
        system_prompt_ids=("contentieux-system",),
    )

    playbook = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.PLAYBOOK,
        "Playbook qualification des faits en contentieux",
        {"steps": ["Identifier les faits", "Qualifier juridiquement", "Évaluer les risques"]},
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    knowledge_pack = deps.knowledge_packs.register_pack(
        "kp-contentieux",
        "Connaissances Contentieux",
        LegalDomain.CIVIL,
        knowledge_object_ids=(playbook.id,),
    )

    pattern = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.REASONING_PATTERN,
        "Argumentation contradictoire en contentieux contractuel",
        {
            "context": "Litige contractuel entre deux professionnels",
            "strategy": "Opposer systématiquement les arguments des deux parties avant conclusion.",
            "arguments": ["Inexécution démontrée", "Préjudice chiffré"],
            "counter_arguments": ["Force majeure invoquée par la partie adverse"],
        },
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    reasoning_pack = deps.reasoning_packs.register_pack(
        "rp-contentieux",
        "Raisonnement Contentieux",
        LegalDomain.CIVIL,
        frozenset(
            {
                ReasoningStrategyType.QUALIFICATION,
                ReasoningStrategyType.CONTRADICTORY_ARGUMENTATION,
                ReasoningStrategyType.RISK_ANALYSIS,
            }
        ),
        pattern_ids=(pattern.id,),
    )

    document_pack = deps.document_packs.register_pack(
        "dp-contentieux",
        "Documents Contentieux",
        LegalDomain.CIVIL,
        document_types=(DocumentType.ASSIGNATION, DocumentType.CONCLUSIONS, DocumentType.MEMOIRE),
    )

    hearing_templates = deps.template_library.list_templates(case_type="preparation_audience")
    workflow_pack = deps.workflow_packs.register_pack(
        "wp-contentieux",
        "Workflows Contentieux",
        LegalDomain.CIVIL,
        workflow_template_ids=tuple(t.id for t in hearing_templates),
    )

    validation_policy = deps.validation_policies.create_policy(
        "vp-contentieux-partner",
        "Validation associé avant dépôt",
        LegalDomain.CIVIL,
        CopilotValidationPolicyType.PARTNER_VALIDATION,
        "Toute assignation ou conclusions doit être validée par un associé avant dépôt.",
        required_role="partner",
    )

    spec = CopilotSpec(
        id="copilot-contentieux",
        name="Copilote Contentieux",
        domain=LegalDomain.CIVIL,
        description=(
            "Assiste la qualification des faits, l'argumentation contradictoire et la "
            "rédaction des actes de procédure en contentieux civil et commercial."
        ),
        version="1.0.0",
        author="tmis-legal-copilot-framework",
        agent_ids=(
            "agent-document-analyst",
            "agent-legal-researcher",
            "agent-jurisprudence-expert",
            "agent-drafter",
            "agent-critic",
        ),
        compatible_models=frozenset({"gpt-4o", "claude-3-5-sonnet"}),
        workflow_pack_ids=(workflow_pack.id,),
        document_pack_ids=(document_pack.id,),
        knowledge_pack_ids=(knowledge_pack.id,),
        reasoning_pack_ids=(reasoning_pack.id,),
        prompt_pack_id=prompt_pack.id,
        validation_policy_ids=(validation_policy.id,),
        permissions=frozenset(
            {
                ExtensionPermission.ACCESS_KNOWLEDGE,
                ExtensionPermission.ACCESS_RESEARCH,
                ExtensionPermission.CREATE_DRAFTS,
            }
        ),
    )
    return deps.builder.build(spec)
