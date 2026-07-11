from tmis.ai_fabric.governance.engine import GovernanceEngine
from tmis.ai_fabric.governance.store import InMemoryGovernanceStore
from tmis.ai_fabric.policies.schemas import Policy, PolicyType, new_policy_id
from tmis.ai_fabric.policies.store import InMemoryPolicyStore
from tmis.platform.licensing.bootstrap import get_license_engine

FIRM = "firm-a"


def _governance_engine() -> tuple[GovernanceEngine, InMemoryPolicyStore]:
    policy_store = InMemoryPolicyStore()
    governance_store = InMemoryGovernanceStore()
    return GovernanceEngine(policy_store, governance_store, get_license_engine()), policy_store


def test_no_policy_is_allowed_by_default() -> None:
    engine, _ = _governance_engine()

    decision = engine.evaluate(FIRM, "gpt-x")

    assert decision.allowed is True
    assert decision.reasons == ("aucune politique restrictive applicable",)


def test_model_forbidden_policy_blocks_the_model() -> None:
    engine, policy_store = _governance_engine()
    policy_store.add(
        Policy(
            id=new_policy_id(),
            type=PolicyType.MODEL_FORBIDDEN,
            model_name="gpt-x",
            reason="non conforme RGPD",
        )
    )

    decision = engine.evaluate(FIRM, "gpt-x")

    assert decision.allowed is False
    assert "modèle interdit" in decision.reasons[0]


def test_enterprise_only_policy_blocks_without_the_feature() -> None:
    engine, policy_store = _governance_engine()
    policy_store.add(
        Policy(
            id=new_policy_id(),
            type=PolicyType.ENTERPRISE_ONLY,
            model_name="gpt-x",
            reason="réservé Enterprise",
        )
    )

    decision = engine.evaluate(FIRM, "gpt-x")

    assert decision.allowed is False


def test_country_restricted_policy() -> None:
    engine, policy_store = _governance_engine()
    policy_store.add(
        Policy(
            id=new_policy_id(),
            type=PolicyType.COUNTRY_RESTRICTED,
            model_name="gpt-x",
            reason="hébergement EU uniquement",
            allowed_countries=frozenset({"FR", "DE"}),
        )
    )

    assert engine.evaluate(FIRM, "gpt-x", country="FR").allowed is True
    assert engine.evaluate(FIRM, "gpt-x", country="US").allowed is False
    assert engine.evaluate(FIRM, "gpt-x").allowed is False


def test_data_type_restricted_policy() -> None:
    engine, policy_store = _governance_engine()
    policy_store.add(
        Policy(
            id=new_policy_id(),
            type=PolicyType.DATA_TYPE_RESTRICTED,
            model_name="gpt-x",
            reason="pas de données de santé",
            allowed_data_types=frozenset({"contract"}),
        )
    )

    assert engine.evaluate(FIRM, "gpt-x", data_type="contract").allowed is True
    assert engine.evaluate(FIRM, "gpt-x", data_type="health").allowed is False


def test_wildcard_policy_applies_to_every_model() -> None:
    engine, policy_store = _governance_engine()
    policy_store.add(
        Policy(id=new_policy_id(), type=PolicyType.MODEL_FORBIDDEN, model_name="*", reason="gel")
    )

    assert engine.evaluate(FIRM, "any-model").allowed is False


def test_deactivated_policy_no_longer_applies() -> None:
    engine, policy_store = _governance_engine()
    policy = Policy(
        id=new_policy_id(), type=PolicyType.MODEL_FORBIDDEN, model_name="gpt-x", reason="test"
    )
    policy_store.add(policy)
    policy_store.deactivate(policy.id)

    assert engine.evaluate(FIRM, "gpt-x").allowed is True


def test_evaluate_records_decision_in_history_by_default() -> None:
    engine, _ = _governance_engine()

    engine.evaluate(FIRM, "gpt-x")

    assert len(engine.history(FIRM, "gpt-x")) == 1


def test_evaluate_with_record_false_does_not_persist() -> None:
    engine, _ = _governance_engine()

    engine.evaluate(FIRM, "gpt-x", record=False)

    assert engine.history(FIRM, "gpt-x") == []
