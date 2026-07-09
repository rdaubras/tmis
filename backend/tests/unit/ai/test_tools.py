import pytest

from tmis.ai.tools.current_datetime_tool import CurrentDatetimeTool
from tmis.ai.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_current_datetime_tool_returns_iso_string() -> None:
    tool = CurrentDatetimeTool()
    result = await tool.run()
    assert isinstance(result, str)
    assert "T" in result


@pytest.mark.asyncio
async def test_registry_run_dispatches_to_registered_tool() -> None:
    registry = ToolRegistry()
    registry.register(CurrentDatetimeTool())
    result = await registry.run("current_datetime")
    assert isinstance(result, str)


def test_registry_get_unknown_tool_raises() -> None:
    registry = ToolRegistry()
    with pytest.raises(ValueError, match="Unknown tool"):
        registry.get("does-not-exist")


def test_registry_list_names() -> None:
    registry = ToolRegistry()
    registry.register(CurrentDatetimeTool())
    assert registry.list_names() == ["current_datetime"]
