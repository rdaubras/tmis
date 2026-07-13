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
    """MVP copilot for droit fiscal: analyse de risques fiscaux et
    consultations. Demonstrates the architecture, not full tax-law
    logic (Sprint 24 Phase 12 scope)."""

    deps.prompt_registry.register(
        "fiscal-system",
        category="system",
        template=(
            "Tu es le copilote Fiscal du cabinet {cabinet}. Analyse le montage {montage} "
            "et identifie les risques de requalification fiscale."
        ),
        variables=("cabinet", "montage"),
    )
    prompt_pack = deps.prompt_packs.register_pack(
        "pp-fiscal",
        "Prompts Droit fiscal",
        LegalDomain.FISCAL,
        system_prompt_ids=("fiscal-system",),
    )

    internal_rule = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.INTERNAL_RULE,
        "Seuils internes de tolérance au risque fiscal",
        {
            "steps": [
                "Évaluer le montage",
                "Comparer au seuil de tolérance",
                "Alerter si dépassement",
            ]
        },
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    knowledge_pack = deps.knowledge_packs.register_pack(
        "kp-fiscal",
        "Connaissances Droit fiscal",
        LegalDomain.FISCAL,
        knowledge_object_ids=(internal_rule.id,),
    )

    pattern = deps.knowledge_space.create(
        deps.firm_id,
        KnowledgeType.REASONING_PATTERN,
        "Analyse de risque de requalification d'un montage",
        {
            "context": "Montage d'optimisation fiscale",
            "strategy": "Comparer le montage aux critères jurisprudentiels de l'abus de droit.",
            "arguments": ["Motif économique documenté"],
            "counter_arguments": ["Montage à but exclusivement fiscal"],
        },
        _FIRM_KNOWLEDGE_AUTHOR,
    )
    reasoning_pack = deps.reasoning_packs.register_pack(
        "rp-fiscal",
        "Raisonnement Droit fiscal",
        LegalDomain.FISCAL,
        frozenset(
            {
                ReasoningStrategyType.RISK_ANALYSIS,
                ReasoningStrategyType.ALTERNATIVE_SEARCH,
                ReasoningStrategyType.CONSISTENCY_CHECK,
            }
        ),
        pattern_ids=(pattern.id,),
    )

    document_pack = deps.document_packs.register_pack(
        "dp-fiscal",
        "Documents Droit fiscal",
        LegalDomain.FISCAL,
        document_types=(
            DocumentType.CONSULTATION,
            DocumentType.NOTE_INTERNE,
            DocumentType.SYNTHESE,
        ),
    )

    validation_templates = deps.template_library.list_templates(case_type="validation_brouillon")
    workflow_pack = deps.workflow_packs.register_pack(
        "wp-fiscal",
        "Workflows Droit fiscal",
        LegalDomain.FISCAL,
        workflow_template_ids=tuple(t.id for t in validation_templates),
    )

    validation_policy = deps.validation_policies.create_policy(
        "vp-fiscal-confidence",
        "Seuil de confiance minimum avant remise",
        LegalDomain.FISCAL,
        CopilotValidationPolicyType.MIN_CONFIDENCE,
        "Une consultation fiscale n'est remise que si le score de confiance dépasse le seuil.",
        min_confidence=0.85,
    )

    spec = CopilotSpec(
        id="copilot-droit-fiscal",
        name="Copilote Droit fiscal",
        domain=LegalDomain.FISCAL,
        description=(
            "Assiste l'analyse des risques fiscaux et la rédaction de consultations : "
            "qualification du montage, comparaison aux seuils de tolérance du cabinet."
        ),
        version="1.0.0",
        author="tmis-legal-copilot-framework",
        agent_ids=(
            "agent-document-analyst",
            "agent-tax-expert",
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
            {ExtensionPermission.ACCESS_KNOWLEDGE, ExtensionPermission.ACCESS_RESEARCH}
        ),
    )
    return deps.builder.build(spec)
