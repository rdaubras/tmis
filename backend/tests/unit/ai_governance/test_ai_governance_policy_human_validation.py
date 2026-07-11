from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.schemas import ValidationDecisionType, ValidationStatus
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.schemas import GovernancePolicyType, PolicyEvaluationContext
from tmis.ai_governance.policy_engine.store import InMemoryGovernancePolicyStore

FIRM = "firm-a"
PRODUCTION = "prod-1"


def _policy_engine() -> PolicyEngine:
    return PolicyEngine(InMemoryGovernancePolicyStore())


def test_evaluate_with_no_policies_is_allowed() -> None:
    engine = _policy_engine()

    evaluation = engine.evaluate(PolicyEvaluationContext(firm_id=FIRM, production_id=PRODUCTION))

    assert evaluation.allowed is True
    assert evaluation.reasons == ("aucune politique restrictive applicable",)


def test_mandatory_validation_before_export_blocks_unvalidated_export() -> None:
    engine = _policy_engine()
    engine.create_policy(
        FIRM, GovernancePolicyType.MANDATORY_VALIDATION_BEFORE_EXPORT, "conformité cabinet"
    )

    context = PolicyEvaluationContext(
        firm_id=FIRM, production_id=PRODUCTION, is_export=True, human_validated=False
    )
    evaluation = engine.evaluate(context)

    assert evaluation.allowed is False


def test_mandatory_validation_before_export_allows_validated_export() -> None:
    engine = _policy_engine()
    engine.create_policy(
        FIRM, GovernancePolicyType.MANDATORY_VALIDATION_BEFORE_EXPORT, "conformité cabinet"
    )

    context = PolicyEvaluationContext(
        firm_id=FIRM, production_id=PRODUCTION, is_export=True, human_validated=True
    )
    evaluation = engine.evaluate(context)

    assert evaluation.allowed is True


def test_min_confidence_threshold_policy() -> None:
    engine = _policy_engine()
    engine.create_policy(
        FIRM, GovernancePolicyType.MIN_CONFIDENCE_THRESHOLD, "seuil qualité", min_confidence=0.7
    )

    below = engine.evaluate(
        PolicyEvaluationContext(firm_id=FIRM, production_id=PRODUCTION, confidence_value=0.5)
    )
    above = engine.evaluate(
        PolicyEvaluationContext(firm_id=FIRM, production_id=PRODUCTION, confidence_value=0.9)
    )

    assert below.allowed is False
    assert above.allowed is True


def test_forbidden_model_policy() -> None:
    engine = _policy_engine()
    engine.create_policy(
        FIRM, GovernancePolicyType.FORBIDDEN_MODEL, "modèle non conforme RGPD",
        forbidden_model_name="mistral-fast",
    )

    context = PolicyEvaluationContext(
        firm_id=FIRM, production_id=PRODUCTION, model_names_used=("mistral-fast",)
    )
    evaluation = engine.evaluate(context)

    assert evaluation.allowed is False


def test_mandatory_citations_policy() -> None:
    engine = _policy_engine()
    engine.create_policy(FIRM, GovernancePolicyType.MANDATORY_CITATIONS, "traçabilité juridique")

    context = PolicyEvaluationContext(firm_id=FIRM, production_id=PRODUCTION, citation_count=0)
    evaluation = engine.evaluate(context)

    assert evaluation.allowed is False


def test_mandatory_review_for_case_type_policy() -> None:
    engine = _policy_engine()
    engine.create_policy(
        FIRM,
        GovernancePolicyType.MANDATORY_REVIEW_FOR_CASE_TYPE,
        "dossiers sensibles",
        case_type="penal",
    )

    context = PolicyEvaluationContext(
        firm_id=FIRM, production_id=PRODUCTION, case_type="penal", human_validated=False
    )
    evaluation = engine.evaluate(context)

    assert evaluation.allowed is False


def test_deactivated_policy_no_longer_applies() -> None:
    engine = _policy_engine()
    policy = engine.create_policy(
        FIRM, GovernancePolicyType.MANDATORY_CITATIONS, "traçabilité juridique"
    )
    engine.deactivate_policy(policy.id)

    context = PolicyEvaluationContext(firm_id=FIRM, production_id=PRODUCTION, citation_count=0)
    evaluation = engine.evaluate(context)

    assert evaluation.allowed is True


def test_policies_are_scoped_per_firm() -> None:
    engine = _policy_engine()
    engine.create_policy(FIRM, GovernancePolicyType.MANDATORY_CITATIONS, "traçabilité juridique")

    assert engine.list_policies("other-firm") == []


def _validation_engine() -> HumanValidationEngine:
    return HumanValidationEngine(InMemoryValidationStore())


def test_simple_validation_settles_on_first_approval() -> None:
    engine = _validation_engine()
    request = engine.request_simple(FIRM, PRODUCTION, "user-1", ("approver-1", "approver-2"))

    result = engine.decide(FIRM, request.id, "approver-1", ValidationDecisionType.APPROVE)

    assert result.status is ValidationStatus.APPROVED


def test_multiple_validation_requires_every_approver() -> None:
    engine = _validation_engine()
    request = engine.request_multiple(FIRM, PRODUCTION, "user-1", ("approver-1", "approver-2"))

    after_first = engine.decide(FIRM, request.id, "approver-1", ValidationDecisionType.APPROVE)
    assert after_first.status is ValidationStatus.PENDING

    after_second = engine.decide(FIRM, request.id, "approver-2", ValidationDecisionType.APPROVE)
    assert after_second.status is ValidationStatus.APPROVED


def test_hierarchical_validation_advances_tier_by_tier() -> None:
    engine = _validation_engine()
    request = engine.request_hierarchical(
        FIRM, PRODUCTION, "user-1", (("associate-1",), ("partner-1",))
    )

    after_tier_one = engine.decide(
        FIRM, request.id, "associate-1", ValidationDecisionType.APPROVE
    )
    assert after_tier_one.status is ValidationStatus.PENDING

    after_tier_two = engine.decide(FIRM, request.id, "partner-1", ValidationDecisionType.APPROVE)
    assert after_tier_two.status is ValidationStatus.APPROVED


def test_reject_anywhere_settles_as_rejected() -> None:
    engine = _validation_engine()
    request = engine.request_multiple(FIRM, PRODUCTION, "user-1", ("approver-1", "approver-2"))

    result = engine.decide(FIRM, request.id, "approver-1", ValidationDecisionType.REJECT)

    assert result.status is ValidationStatus.REJECTED


def test_request_revision_settles_as_revision_requested() -> None:
    engine = _validation_engine()
    request = engine.request_simple(FIRM, PRODUCTION, "user-1", ("approver-1",))

    result = engine.decide(
        FIRM, request.id, "approver-1", ValidationDecisionType.REQUEST_REVISION
    )

    assert result.status is ValidationStatus.REVISION_REQUESTED


def test_decide_on_unknown_request_raises_key_error() -> None:
    engine = _validation_engine()

    try:
        engine.decide(FIRM, "unknown-id", "approver-1", ValidationDecisionType.APPROVE)
        raised = False
    except KeyError:
        raised = True
    assert raised


def test_is_validated_reflects_approved_status() -> None:
    engine = _validation_engine()
    request = engine.request_simple(FIRM, PRODUCTION, "user-1", ("approver-1",))
    assert engine.is_validated(FIRM, PRODUCTION) is False

    engine.decide(FIRM, request.id, "approver-1", ValidationDecisionType.APPROVE)

    assert engine.is_validated(FIRM, PRODUCTION) is True


def test_validation_history_is_scoped_per_production() -> None:
    engine = _validation_engine()
    engine.request_simple(FIRM, "prod-a", "user-1", ("approver-1",))

    assert engine.history(FIRM, "prod-b") == []
