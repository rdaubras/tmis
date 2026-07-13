import pytest

from tmis.ai_governance.human_validation.engine import HumanValidationEngine
from tmis.ai_governance.human_validation.store import InMemoryValidationStore
from tmis.ai_governance.policy_engine.engine import PolicyEngine
from tmis.ai_governance.policy_engine.schemas import PolicyEvaluationContext
from tmis.ai_governance.policy_engine.store import InMemoryGovernancePolicyStore
from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.validation_policies.engine import ValidationPolicyEngine
from tmis.legal_copilot_framework.validation_policies.schemas import CopilotValidationPolicyType
from tmis.legal_copilot_framework.validation_policies.store import (
    InMemoryCopilotValidationPolicyStore,
)

FIRM = "firm-a"


def _engine() -> ValidationPolicyEngine:
    return ValidationPolicyEngine(
        InMemoryCopilotValidationPolicyStore(),
        PolicyEngine(InMemoryGovernancePolicyStore()),
        HumanValidationEngine(InMemoryValidationStore()),
    )


def test_create_policy_and_get_roundtrip() -> None:
    engine = _engine()
    policy = engine.create_policy(
        "vp-1",
        "Seuil de confiance",
        LegalDomain.FISCAL,
        CopilotValidationPolicyType.MIN_CONFIDENCE,
        "Seuil minimum requis",
        min_confidence=0.8,
    )

    assert engine.get("vp-1") == policy


def test_get_unknown_policy_raises_key_error() -> None:
    engine = _engine()
    with pytest.raises(KeyError):
        engine.get("missing")


def test_attach_to_firm_creates_matching_governance_policy() -> None:
    engine = _engine()
    engine.create_policy(
        "vp-1",
        "Seuil de confiance",
        LegalDomain.FISCAL,
        CopilotValidationPolicyType.MIN_CONFIDENCE,
        "Seuil minimum requis",
        min_confidence=0.8,
    )

    governance_policy = engine.attach_to_firm(FIRM, "vp-1")

    assert governance_policy.firm_id == FIRM
    assert governance_policy.min_confidence == 0.8


def test_attach_to_firm_rejects_double_validation() -> None:
    engine = _engine()
    engine.create_policy(
        "vp-1",
        "Double validation",
        LegalDomain.COMMERCIAL,
        CopilotValidationPolicyType.DOUBLE_VALIDATION,
        "Deux validations requises",
    )

    with pytest.raises(ValueError, match="no automated PolicyEngine equivalent"):
        engine.attach_to_firm(FIRM, "vp-1")


def test_request_validation_uses_multiple_mode_for_double_validation() -> None:
    engine = _engine()
    engine.create_policy(
        "vp-1",
        "Double validation",
        LegalDomain.COMMERCIAL,
        CopilotValidationPolicyType.DOUBLE_VALIDATION,
        "Deux validations requises",
    )

    request = engine.request_validation(FIRM, "prod-1", "requester", "vp-1", ("a1", "a2"))

    assert request.production_id == "prod-1"


def test_request_validation_rejects_automated_policy_types() -> None:
    engine = _engine()
    engine.create_policy(
        "vp-1",
        "Seuil de confiance",
        LegalDomain.FISCAL,
        CopilotValidationPolicyType.MIN_CONFIDENCE,
        "Seuil minimum requis",
        min_confidence=0.8,
    )

    with pytest.raises(ValueError, match="evaluated automatically"):
        engine.request_validation(FIRM, "prod-1", "requester", "vp-1", ("a1",))


def test_evaluate_delegates_to_policy_engine() -> None:
    engine = _engine()
    engine.create_policy(
        "vp-1",
        "Seuil de confiance",
        LegalDomain.FISCAL,
        CopilotValidationPolicyType.MIN_CONFIDENCE,
        "Confiance insuffisante",
        min_confidence=0.9,
    )
    engine.attach_to_firm(FIRM, "vp-1")

    evaluation = engine.evaluate(
        PolicyEvaluationContext(firm_id=FIRM, production_id="prod-1", confidence_value=0.5)
    )

    assert evaluation.allowed is False
