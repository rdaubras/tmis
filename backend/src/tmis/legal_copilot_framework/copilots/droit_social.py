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
    """MVP copilot for droit social: procédures disciplinaires et
    ruptures du contrat de travail. Demonstrates the architecture, not
    full social-law logic (Sprint 24 Phase 12 scope)."""

    deps.prompt_registry.register(
        "social-system",
        category="system",
        template=(
            "Tu es le copilote Droit social du cabinet {cabinet}. Analyse la situation "
            "{situation} du salarié et identifie la procédure applicable."
        ),
        variables=("cabinet", "situation"),
    )
    prompt_pack = deps.prompt_packs.register_pack(
        "pp-social",
        "Prompts Droit social",
        LegalDomain.SOCIAL,
        system_prompt_ids=("social-system",),
    )

    checklist = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.CHECKLIST,
        "Checklist procédure de licenciement",
        {"steps": ["Convocation à l'entretien", "Entretien préalable", "Notification motivée"]},
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    knowledge_pack = deps.knowledge_packs.register_pack(
        "kp-social",
        "Connaissances Droit social",
        LegalDomain.SOCIAL,
        knowledge_object_ids=(checklist.id,),
    )

    pattern = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.REASONING_PATTERN,
        "Qualification de la cause réelle et sérieuse",
        {
            "context": "Rupture du contrat de travail",
            "strategy": (
                "Comparer les faits reprochés à la jurisprudence sur la cause réelle et sérieuse."
            ),
            "arguments": ["Faute caractérisée et documentée"],
            "counter_arguments": ["Absence de mise en garde préalable"],
        },
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    reasoning_pack = deps.reasoning_packs.register_pack(
        "rp-social",
        "Raisonnement Droit social",
        LegalDomain.SOCIAL,
        frozenset(
            {
                ReasoningStrategyType.QUALIFICATION,
                ReasoningStrategyType.JURISPRUDENCE_COMPARISON,
                ReasoningStrategyType.RISK_ANALYSIS,
            }
        ),
        pattern_ids=(pattern.id,),
    )

    document_pack = deps.document_packs.register_pack(
        "dp-social",
        "Documents Droit social",
        LegalDomain.SOCIAL,
        document_types=(
            DocumentType.CONSULTATION,
            DocumentType.COURRIER,
            DocumentType.MISE_EN_DEMEURE,
        ),
    )

    termination_templates = deps.template_library.list_templates(case_type="mise_en_demeure")
    workflow_pack = deps.workflow_packs.register_pack(
        "wp-social",
        "Workflows Droit social",
        LegalDomain.SOCIAL,
        workflow_template_ids=tuple(t.id for t in termination_templates),
    )

    validation_policy = deps.validation_policies.create_policy(
        "vp-social-review",
        "Revue humaine obligatoire avant notification",
        LegalDomain.SOCIAL,
        CopilotValidationPolicyType.MANDATORY_HUMAN_REVIEW,
        "Toute notification de rupture doit être revue par un avocat avant envoi.",
    )

    spec = CopilotSpec(
        id="copilot-droit-social",
        name="Copilote Droit social",
        domain=LegalDomain.SOCIAL,
        description=(
            "Assiste les procédures disciplinaires et de rupture du contrat de travail : "
            "qualification de la cause, checklist procédurale, courriers de notification."
        ),
        version="1.0.0",
        author="tmis-legal-copilot-framework",
        agent_ids=(
            "agent-document-analyst",
            "agent-social-law-expert",
            "agent-legal-researcher",
            "agent-drafter",
            "agent-verifier",
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
                ExtensionPermission.CREATE_DRAFTS,
                ExtensionPermission.READ_CASES,
            }
        ),
    )
    return deps.builder.build(spec)
