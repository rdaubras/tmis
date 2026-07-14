from datetime import UTC, datetime, timedelta

from tmis.legal_knowledge_graph.governance.engine import GraphAccessPolicyEngine
from tmis.legal_knowledge_graph.governance.store import InMemoryNodeAccessPolicyStore

FIRM = "firm-a"
NODE = "node-1"


def _engine() -> GraphAccessPolicyEngine:
    return GraphAccessPolicyEngine(InMemoryNodeAccessPolicyStore())


def test_get_policy_for_unset_node_returns_none() -> None:
    engine = _engine()

    assert engine.get_policy(FIRM, NODE) is None


def test_abac_attributes_default_to_standard_confidentiality() -> None:
    engine = _engine()

    attributes = engine.abac_attributes_for(FIRM, NODE)

    assert attributes.confidentiality_level == "standard"


def test_set_policy_updates_abac_attributes() -> None:
    engine = _engine()
    engine.set_policy(FIRM, NODE, confidentiality_level="confidential", retention_days=3650)

    attributes = engine.abac_attributes_for(FIRM, NODE)
    policy = engine.get_policy(FIRM, NODE)

    assert attributes.confidentiality_level == "confidential"
    assert policy is not None
    assert policy.retention_days == 3650


def test_is_past_retention_false_when_no_retention_configured() -> None:
    engine = _engine()
    engine.set_policy(FIRM, NODE, confidentiality_level="standard")

    assert engine.is_past_retention(FIRM, NODE) is False


def test_is_past_retention_true_once_window_elapsed() -> None:
    engine = _engine()
    engine.set_policy(FIRM, NODE, confidentiality_level="standard", retention_days=30)

    future = datetime.now(UTC) + timedelta(days=31)

    assert engine.is_past_retention(FIRM, NODE, as_of=future) is True
