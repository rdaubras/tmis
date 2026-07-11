import uuid
from abc import ABC, abstractmethod
from typing import Any

from tmis.ai.schemas.agent import AgentInput, AgentOutput
from tmis.platform_sdk.plugin_system.schemas import PluginType
from tmis.platform_sdk.sdk.schemas import PluginContext


class BaseAgentPlugin(ABC):
    """The sprint's "AGENT SDK": déclarer ses capacités, recevoir un
    contexte, utiliser les services du TMIS AI Kernel, publier des
    événements. Subclass and implement `capabilities`/`run()` —
    `invoke()` is the fixed adapter to the uniform `PluginPort`
    contract every plugin type shares (see
    `tmis.platform_sdk.sdk.ports.PluginPort`). Kernel access is only
    ever through `context.kernel`
    (`tmis.ai_team.agents.ports.KernelPort`, Sprint 11) — an agent
    plugin never imports a Kernel provider directly, the same
    constraint `tmis.ai_team` agents already respect."""

    plugin_type = PluginType.AGENT

    def __init__(self, plugin_id: str) -> None:
        self.id = plugin_id

    @property
    @abstractmethod
    def capabilities(self) -> tuple[str, ...]:
        """The skills this agent declares, e.g. `("fiscal_analysis",)`."""

    @abstractmethod
    async def run(self, context: PluginContext, agent_input: AgentInput) -> AgentOutput: ...

    async def invoke(self, context: PluginContext, payload: dict[str, Any]) -> dict[str, Any]:
        agent_input = AgentInput(
            task_id=uuid.UUID(str(payload["task_id"])) if "task_id" in payload else uuid.uuid4(),
            case_id=uuid.UUID(str(payload["case_id"])) if payload.get("case_id") else None,
            context=dict(payload.get("context", {})),
        )
        output = await self.run(context, agent_input)
        await context.events.publish(
            "AIWorkflowFinished",
            {"plugin_id": self.id, "confidence": output.confidence.value},
        )
        return {
            "result": output.result,
            "confidence": output.confidence.value,
            "warnings": list(output.warnings),
        }
