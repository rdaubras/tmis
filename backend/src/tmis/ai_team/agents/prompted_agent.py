from tmis.ai.schemas.agent import AgentInput, AgentOutput, ConfidenceLevel
from tmis.ai_team.agents.ports import KernelPort
from tmis.ai_team.agents.schemas import AgentRole


class PromptedTeamAgent:
    """Implements `TeamAgentPort`: a generic, role-parameterized agent
    that turns its `system_prompt` plus the task's context into one
    `KernelPort.complete()` call (see docs/53-guide-creation-agent.md).
    Every non-Coordinator role in the default catalog is an instance of
    this class rather than a bespoke subclass — the roles differ only
    in *what* they ask the model, never in *how* they call it, so a
    single class serving ten roles is simpler than ten near-identical
    subclasses. A future agent needing genuinely different behavior
    (e.g. calling `search_connectors` first) can still implement
    `TeamAgentPort` directly without touching this class."""

    def __init__(
        self, name: str, role: AgentRole, system_prompt: str, kernel: KernelPort
    ) -> None:
        self.name = name
        self.role = role
        self._system_prompt = system_prompt
        self._kernel = kernel

    async def run(self, agent_input: AgentInput) -> AgentOutput:
        context_text = "\n".join(f"{key}: {value}" for key, value in agent_input.context.items())
        prompt = f"{self._system_prompt}\n\nContexte de la mission:\n{context_text}"
        completion = await self._kernel.complete(prompt)
        return AgentOutput(
            result={"agent_role": self.role.value, "text": completion},
            confidence=ConfidenceLevel.MEDIUM,
            warnings=["Production à valider par un professionnel du droit."],
        )
