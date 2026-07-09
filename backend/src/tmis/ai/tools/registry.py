from tmis.ai.tools.ports import ToolPort


class ToolRegistry:
    """Registers tools by name so agents can discover and invoke them
    through the Kernel rather than importing implementation code."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolPort] = {}

    def register(self, tool: ToolPort) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> ToolPort:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ValueError(f"Unknown tool: {name!r}") from exc

    def list_names(self) -> list[str]:
        return list(self._tools)

    async def run(self, name: str, **kwargs: object) -> object:
        return await self.get(name).run(**kwargs)
