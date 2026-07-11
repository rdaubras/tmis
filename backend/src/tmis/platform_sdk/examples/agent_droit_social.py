"""The sprint's "Agent Droit Social" example plugin — a second agent
built on `tmis.platform_sdk.agent_sdk`, demonstrating that the SDK
supports more than one specialization without any change to the SDK
itself."""

from tmis.ai.schemas.agent import AgentInput, AgentOutput, ConfidenceLevel
from tmis.platform_sdk.agent_sdk.base import BaseAgentPlugin
from tmis.platform_sdk.sdk.schemas import PluginContext

PLUGIN_ID = "agent-droit-social"


class AgentDroitSocialPlugin(BaseAgentPlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id=PLUGIN_ID)

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("social_law_analysis",)

    async def run(self, context: PluginContext, agent_input: AgentInput) -> AgentOutput:
        question = str(agent_input.context.get("question", ""))
        if context.kernel is not None:
            text = await context.kernel.complete(
                f"En tant qu'expert en droit social, réponds à : {question}"
            )
        else:
            text = f"[agent-droit-social] analyse de droit social de : {question}"
        return AgentOutput(
            result={"agent_role": "social_law_expert", "text": text},
            confidence=ConfidenceLevel.MEDIUM,
            warnings=["Production à valider par un professionnel du droit."],
        )
