"""The sprint's "Agent Fiscal" example plugin — demonstrates
`tmis.platform_sdk.agent_sdk`. Purely illustrative, as the sprint asks
("ces exemples servent uniquement de démonstration de l'architecture")."""

from tmis.ai.schemas.agent import AgentInput, AgentOutput, ConfidenceLevel
from tmis.platform_sdk.agent_sdk.base import BaseAgentPlugin
from tmis.platform_sdk.sdk.schemas import PluginContext

PLUGIN_ID = "agent-fiscal"


class AgentFiscalPlugin(BaseAgentPlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id=PLUGIN_ID)

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("fiscal_analysis",)

    async def run(self, context: PluginContext, agent_input: AgentInput) -> AgentOutput:
        question = str(agent_input.context.get("question", ""))
        if context.kernel is not None:
            text = await context.kernel.complete(
                f"En tant qu'expert fiscal, réponds à : {question}"
            )
        else:
            text = f"[agent-fiscal] analyse fiscale de : {question}"
        return AgentOutput(
            result={"agent_role": "fiscal_expert", "text": text},
            confidence=ConfidenceLevel.MEDIUM,
            warnings=["Production à valider par un professionnel du droit."],
        )
