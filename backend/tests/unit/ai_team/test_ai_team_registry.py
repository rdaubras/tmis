from tmis.ai_team.agents.catalog import default_descriptors
from tmis.ai_team.agents.schemas import AgentRole
from tmis.ai_team.registry.schemas import AgentDescriptor
from tmis.ai_team.registry.store import InMemoryAgentRegistry


def test_default_catalog_has_ten_agents_covering_every_role() -> None:
    descriptors = default_descriptors()

    assert len(descriptors) == 10
    roles = {d.role for d in descriptors}
    assert AgentRole.COORDINATOR not in roles
    assert AgentRole.DOCUMENT_ANALYST in roles
    assert AgentRole.GDPR_EXPERT in roles


def test_register_is_dynamic() -> None:
    registry = InMemoryAgentRegistry()
    assert registry.list_all() == []

    registry.register(
        AgentDescriptor(
            id="agent-custom",
            name="Agent Custom",
            role=AgentRole.CRITIC,
            description="A marketplace agent registered at runtime.",
            skills=frozenset({"critique"}),
        )
    )

    assert len(registry.list_all()) == 1
    assert registry.get("agent-custom") is not None


def test_list_by_role_filters_correctly() -> None:
    registry = InMemoryAgentRegistry()
    for descriptor in default_descriptors():
        registry.register(descriptor)

    verifiers = registry.list_by_role(AgentRole.VERIFIER)

    assert len(verifiers) == 1
    assert verifiers[0].id == "agent-verifier"


def test_list_by_skill_filters_correctly() -> None:
    registry = InMemoryAgentRegistry()
    for descriptor in default_descriptors():
        registry.register(descriptor)

    risk_capable = registry.list_by_skill("risk_analysis")

    assert {d.id for d in risk_capable} == {
        "agent-gdpr-expert",
        "agent-tax-expert",
        "agent-social-law-expert",
    }


def test_get_unknown_agent_returns_none() -> None:
    registry = InMemoryAgentRegistry()

    assert registry.get("does-not-exist") is None
