from typing import Protocol

from tmis.ai.events.events import Event
from tmis.ai.schemas.agent import AgentOutput
from tmis.ai.schemas.connector import ConnectorDocument
from tmis.ai.schemas.provider import ModelResponse


class KernelFacadePort(Protocol):
    """Everything a LangGraph node is allowed to use from the Kernel.

    Keeping this surface small and explicit is what lets nodes stay
    decoupled from `tmis.ai.kernel.TMISKernel` (no circular import) and
    keeps agents from reaching past the Kernel into a provider or
    connector directly.
    """

    async def complete(self, prompt: str) -> ModelResponse: ...

    async def search_connectors(self, query: str) -> list[ConnectorDocument]: ...

    async def publish_event(self, event: Event) -> None: ...

    def validate_output(self, output: AgentOutput) -> list[str]: ...
