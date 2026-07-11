import uuid

from tmis.ai.schemas.agent import AgentInput
from tmis.ai_team.agents.catalog import build_default_agents, default_descriptors
from tmis.ai_team.agents.kernel_adapter import KernelAgentAdapter
from tmis.ai_team.agents.prompted_agent import PromptedTeamAgent
from tmis.ai_team.agents.schemas import AgentRole


class _FakeKernel:
    def __init__(self, response: str = "réponse simulée") -> None:
        self._response = response
        self.last_prompt: str | None = None

    async def complete(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self._response


async def test_prompted_agent_wraps_kernel_response_in_agent_output() -> None:
    kernel = _FakeKernel("analyse terminée")
    agent = PromptedTeamAgent("Analyste", AgentRole.DOCUMENT_ANALYST, "system prompt", kernel)

    output = await agent.run(AgentInput(task_id=uuid.uuid4(), case_id=None, context={}))

    assert output.result["text"] == "analyse terminée"
    assert output.result["agent_role"] == "document_analyst"
    assert output.warnings


async def test_prompted_agent_includes_context_in_the_prompt() -> None:
    kernel = _FakeKernel()
    agent = PromptedTeamAgent("Analyste", AgentRole.DOCUMENT_ANALYST, "system prompt", kernel)

    await agent.run(
        AgentInput(
            task_id=uuid.uuid4(), case_id=None, context={"case_summary": "Litige commercial"}
        )
    )

    assert "case_summary: Litige commercial" in (kernel.last_prompt or "")
    assert "system prompt" in (kernel.last_prompt or "")


def test_build_default_agents_creates_one_instance_per_descriptor() -> None:
    agents = build_default_agents(_FakeKernel())

    descriptor_ids = {d.id for d in default_descriptors()}
    assert set(agents.keys()) == descriptor_ids


def test_every_default_agent_has_a_matching_role_and_name() -> None:
    agents = build_default_agents(_FakeKernel())

    for descriptor in default_descriptors():
        agent = agents[descriptor.id]
        assert agent.role == descriptor.role
        assert agent.name == descriptor.name


async def test_kernel_agent_adapter_unwraps_model_response_text() -> None:
    class _FakeTMISKernel:
        async def complete(self, prompt: str):  # type: ignore[no-untyped-def]
            class _Resp:
                text = f"echo: {prompt}"

            return _Resp()

    adapter = KernelAgentAdapter(_FakeTMISKernel())  # type: ignore[arg-type]

    result = await adapter.complete("hello")

    assert result == "echo: hello"
