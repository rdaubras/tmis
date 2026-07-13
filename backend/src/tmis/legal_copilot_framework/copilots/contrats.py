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
    """MVP copilot for la revue contractuelle: analyse de clauses et
    détection de risques dans les contrats commerciaux. Uses
    `LegalDomain.COMMERCIAL` — same reuse rationale as the "Droit des
    sociétés" copilot (see that module's docstring). Demonstrates the
    architecture, not full contract-law logic (Sprint 24 Phase 12
    scope)."""

    deps.prompt_registry.register(
        "contrats-system",
        category="system",
        template=(
            "Tu es le copilote Contrats du cabinet {cabinet}. Analyse le contrat {contrat} "
            "et identifie les clauses à risque pour le client."
        ),
        variables=("cabinet", "contrat"),
    )
    prompt_pack = deps.prompt_packs.register_pack(
        "pp-contrats",
        "Prompts Contrats",
        LegalDomain.COMMERCIAL,
        system_prompt_ids=("contrats-system",),
    )

    clause = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.CLAUSE,
        "Clause de limitation de responsabilité type",
        {
            "steps": [
                "Identifier le plafond",
                "Vérifier les exclusions",
                "Comparer au standard du cabinet",
            ]
        },
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    knowledge_pack = deps.knowledge_packs.register_pack(
        "kp-contrats",
        "Connaissances Contrats",
        LegalDomain.COMMERCIAL,
        knowledge_object_ids=(clause.id,),
    )

    pattern = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.REASONING_PATTERN,
        "Détection de clauses déséquilibrées",
        {
            "context": "Revue d'un contrat commercial",
            "strategy": "Comparer chaque clause au standard du cabinet et signaler les écarts.",
            "arguments": ["Clause conforme au standard négocié"],
            "counter_arguments": ["Clause de non-concurrence disproportionnée"],
        },
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    reasoning_pack = deps.reasoning_packs.register_pack(
        "rp-contrats",
        "Raisonnement Contrats",
        LegalDomain.COMMERCIAL,
        frozenset(
            {
                ReasoningStrategyType.CONSISTENCY_CHECK,
                ReasoningStrategyType.RISK_ANALYSIS,
                ReasoningStrategyType.ALTERNATIVE_SEARCH,
            }
        ),
        pattern_ids=(pattern.id,),
    )

    document_pack = deps.document_packs.register_pack(
        "dp-contrats",
        "Documents Contrats",
        LegalDomain.COMMERCIAL,
        document_types=(
            DocumentType.CONSULTATION,
            DocumentType.SYNTHESE,
            DocumentType.NOTE_INTERNE,
        ),
    )

    review_templates = deps.template_library.list_templates(case_type="revue_contractuelle")
    workflow_pack = deps.workflow_packs.register_pack(
        "wp-contrats",
        "Workflows Contrats",
        LegalDomain.COMMERCIAL,
        workflow_template_ids=tuple(t.id for t in review_templates),
    )

    validation_policy = deps.validation_policies.create_policy(
        "vp-contrats-role",
        "Revue contractuelle réservée aux avocats",
        LegalDomain.COMMERCIAL,
        CopilotValidationPolicyType.ROLE_RESTRICTION,
        "Seul un avocat peut valider une note de revue contractuelle avant remise au client.",
        required_role="lawyer",
    )

    spec = CopilotSpec(
        id="copilot-contrats",
        name="Copilote Contrats",
        domain=LegalDomain.COMMERCIAL,
        description=(
            "Assiste la revue contractuelle : détection de clauses à risque, comparaison "
            "aux standards du cabinet, synthèse des points de négociation."
        ),
        version="1.0.0",
        author="tmis-legal-copilot-framework",
        agent_ids=(
            "agent-document-analyst",
            "agent-drafter",
            "agent-verifier",
            "agent-quality-controller",
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
                ExtensionPermission.READ_DOCUMENTS,
                ExtensionPermission.ACCESS_KNOWLEDGE,
                ExtensionPermission.CREATE_DRAFTS,
            }
        ),
    )
    return deps.builder.build(spec)
