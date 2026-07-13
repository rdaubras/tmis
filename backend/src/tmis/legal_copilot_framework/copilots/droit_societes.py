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
    """MVP copilot for droit des sociétés: constitution, gouvernance et
    opérations sur titres. Uses `LegalDomain.COMMERCIAL` — the enum has
    no dedicated "corporate" member and this sprint only extends
    enums where a genuinely new concept is introduced (see the audit
    report); several copilots sharing one broad domain is expected.
    Demonstrates the architecture, not full company-law logic."""

    deps.prompt_registry.register(
        "societes-system",
        category="system",
        template=(
            "Tu es le copilote Droit des sociétés du cabinet {cabinet}. Analyse l'opération "
            "{operation} sur la société {societe} et identifie les formalités requises."
        ),
        variables=("cabinet", "operation", "societe"),
    )
    prompt_pack = deps.prompt_packs.register_pack(
        "pp-societes",
        "Prompts Droit des sociétés",
        LegalDomain.COMMERCIAL,
        system_prompt_ids=("societes-system",),
    )

    best_practice = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.BEST_PRACTICE,
        "Bonnes pratiques de constitution de société",
        {"steps": ["Vérifier la dénomination", "Rédiger les statuts", "Déposer au greffe"]},
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    knowledge_pack = deps.knowledge_packs.register_pack(
        "kp-societes",
        "Connaissances Droit des sociétés",
        LegalDomain.COMMERCIAL,
        knowledge_object_ids=(best_practice.id,),
    )

    pattern = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.REASONING_PATTERN,
        "Choix de la forme sociale adaptée",
        {
            "context": "Constitution d'une nouvelle société",
            "strategy": "Comparer les formes sociales disponibles avant de recommander.",
            "arguments": ["SAS pour la souplesse statutaire", "SARL pour la stabilité"],
            "counter_arguments": ["Coût de constitution plus élevé en SAS"],
        },
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    reasoning_pack = deps.reasoning_packs.register_pack(
        "rp-societes",
        "Raisonnement Droit des sociétés",
        LegalDomain.COMMERCIAL,
        frozenset(
            {
                ReasoningStrategyType.QUALIFICATION,
                ReasoningStrategyType.ALTERNATIVE_SEARCH,
                ReasoningStrategyType.CONSISTENCY_CHECK,
            }
        ),
        pattern_ids=(pattern.id,),
    )

    document_pack = deps.document_packs.register_pack(
        "dp-societes",
        "Documents Droit des sociétés",
        LegalDomain.COMMERCIAL,
        document_types=(DocumentType.NOTE_INTERNE, DocumentType.SYNTHESE, DocumentType.COURRIER),
    )

    opening_templates = deps.template_library.list_templates(case_type="ouverture_dossier")
    workflow_pack = deps.workflow_packs.register_pack(
        "wp-societes",
        "Workflows Droit des sociétés",
        LegalDomain.COMMERCIAL,
        workflow_template_ids=tuple(t.id for t in opening_templates),
    )

    validation_policy = deps.validation_policies.create_policy(
        "vp-societes-double",
        "Double validation avant dépôt au greffe",
        LegalDomain.COMMERCIAL,
        CopilotValidationPolicyType.DOUBLE_VALIDATION,
        "Toute formalité déposée au greffe requiert la validation de deux avocats.",
    )

    spec = CopilotSpec(
        id="copilot-droit-societes",
        name="Copilote Droit des sociétés",
        domain=LegalDomain.COMMERCIAL,
        description=(
            "Assiste la constitution, la gouvernance et les opérations sur titres des "
            "sociétés : choix de la forme sociale, formalités, documentation interne."
        ),
        version="1.0.0",
        author="tmis-legal-copilot-framework",
        agent_ids=(
            "agent-document-analyst",
            "agent-legal-researcher",
            "agent-drafter",
            "agent-verifier",
            "agent-quality-controller",
        ),
        compatible_models=frozenset({"gpt-4o", "claude-3-5-sonnet"}),
        workflow_pack_ids=(workflow_pack.id,),
        document_pack_ids=(document_pack.id,),
        knowledge_pack_ids=(knowledge_pack.id,),
        reasoning_pack_ids=(reasoning_pack.id,),
        prompt_pack_id=prompt_pack.id,
        validation_policy_ids=(validation_policy.id,),
        permissions=frozenset(
            {ExtensionPermission.ACCESS_KNOWLEDGE, ExtensionPermission.CREATE_DRAFTS}
        ),
    )
    return deps.builder.build(spec)
