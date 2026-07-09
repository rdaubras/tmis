from typing import Protocol


class ToolPort(Protocol):
    """A callable capability an agent can invoke through the Kernel's
    `ToolRegistry`, instead of importing arbitrary code directly."""

    name: str
    description: str

    async def run(self, **kwargs: object) -> object: ...
