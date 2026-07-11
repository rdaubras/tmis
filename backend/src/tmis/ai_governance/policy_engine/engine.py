from tmis.ai_governance.policy_engine.ports import GovernancePolicyStorePort
from tmis.ai_governance.policy_engine.schemas import (
    GovernancePolicyType,
    PolicyEvaluation,
    PolicyEvaluationContext,
    new_policy_evaluation_id,
)


class PolicyEngine:
    """The sprint's "POLICY ENGINE": evaluates a production against
    every active policy configured for its firm. No production is
    considered final if it fails an applicable policy — the sprint's
    "aucune réponse IA ne doit être considérée comme définitive sans
    respecter les politiques configurées par le cabinet"."""

    def __init__(self, store: GovernancePolicyStorePort) -> None:
        self._store = store

    def evaluate(self, context: PolicyEvaluationContext) -> PolicyEvaluation:
        reasons: list[str] = []
        allowed = True

        for policy in self._store.list_for_firm(context.firm_id):
            match policy.type:
                case GovernancePolicyType.MANDATORY_VALIDATION_BEFORE_EXPORT:
                    if context.is_export and not context.human_validated:
                        allowed = False
                        reasons.append(
                            f"validation humaine obligatoire avant export : {policy.reason}"
                        )
                case GovernancePolicyType.MIN_CONFIDENCE_THRESHOLD:
                    threshold = (
                        policy.min_confidence if policy.min_confidence is not None else 0.0
                    )
                    if (
                        context.confidence_value is not None
                        and context.confidence_value < threshold
                    ):
                        allowed = False
                        reasons.append(
                            f"confiance {context.confidence_value:.2f} sous le seuil "
                            f"{threshold:.2f} : {policy.reason}"
                        )
                case GovernancePolicyType.FORBIDDEN_MODEL:
                    if policy.forbidden_model_name in context.model_names_used:
                        allowed = False
                        reasons.append(
                            f"modèle interdit utilisé ({policy.forbidden_model_name}) : "
                            f"{policy.reason}"
                        )
                case GovernancePolicyType.MANDATORY_CITATIONS:
                    if context.citation_count is not None and context.citation_count == 0:
                        allowed = False
                        reasons.append(f"citations obligatoires manquantes : {policy.reason}")
                case GovernancePolicyType.MANDATORY_REVIEW_FOR_CASE_TYPE:
                    if policy.case_type == context.case_type and not context.human_validated:
                        allowed = False
                        reasons.append(
                            f"relecture obligatoire pour ce type de dossier "
                            f"({policy.case_type}) : {policy.reason}"
                        )

        if not reasons:
            reasons.append("aucune politique restrictive applicable")

        return PolicyEvaluation(
            id=new_policy_evaluation_id(),
            firm_id=context.firm_id,
            production_id=context.production_id,
            allowed=allowed,
            reasons=tuple(reasons),
        )
