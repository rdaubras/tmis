import uuid
from typing import TypedDict

from tmis.ai.schemas.agent import AgentOutput
from tmis.ai.schemas.connector import ConnectorDocument


class KernelWorkflowState(TypedDict):
    workflow_id: uuid.UUID
    question: str
    analysis: AgentOutput | None
    research: list[ConnectorDocument]
    verification_warnings: list[str]
    response: str | None
