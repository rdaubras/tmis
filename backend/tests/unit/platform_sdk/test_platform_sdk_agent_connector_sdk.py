from tmis.ai.schemas.agent import AgentInput, AgentOutput, ConfidenceLevel
from tmis.platform_sdk.agent_sdk.base import BaseAgentPlugin
from tmis.platform_sdk.connector_sdk.base import BaseConnectorPlugin
from tmis.platform_sdk.connector_sdk.schemas import ConnectorPage
from tmis.platform_sdk.events_sdk.bus import PlatformEventBus
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.sdk.schemas import PluginContext

FIRM = "firm-a"
PLUGIN = "p1"


def _context(events: PlatformEventBus) -> PluginContext:
    permissions = PermissionEngine(InMemoryPermissionStore())
    return PluginContext(
        firm_id=FIRM,
        actor_id="avocat1",
        plugin_id=PLUGIN,
        events=events,
        permissions=permissions.checker_for(FIRM, PLUGIN),
    )


class _EchoAgent(BaseAgentPlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id=PLUGIN)

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("echo",)

    async def run(self, context: PluginContext, agent_input: AgentInput) -> AgentOutput:
        return AgentOutput(
            result={"text": agent_input.context.get("question"), "case_id": agent_input.case_id},
            confidence=ConfidenceLevel.HIGH,
        )


async def test_agent_plugin_invoke_adapts_payload_and_publishes_event() -> None:
    events = PlatformEventBus()
    agent = _EchoAgent()

    result = await agent.invoke(_context(events), {"context": {"question": "Q?"}})

    assert result["result"]["text"] == "Q?"
    assert result["confidence"] == "high"
    assert len(events.history) == 1
    assert events.history[0].event_name == "AIWorkflowFinished"


async def test_agent_plugin_invoke_no_longer_raises_on_a_non_uuid_case_id() -> None:
    """Sprint 42: `invoke()` used to build `AgentInput.case_id` via
    `uuid.UUID(str(payload["case_id"]))`, which raised an uncaught
    `ValueError` for any non-UUID case id (`CaseStorePort` accepts
    free-form ids). Since `AgentInput.case_id` is now `str | None`,
    `invoke()` passes the case id through as-is instead of crashing."""
    agent = _EchoAgent()

    result = await agent.invoke(_context(PlatformEventBus()), {"case_id": "case-1"})

    assert result["result"]["case_id"] == "case-1"


_DOCS = ({"id": "1", "title": "Alpha"}, {"id": "2", "title": "Beta"})


class _FakeConnector(BaseConnectorPlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id=PLUGIN)
        self.fetch_calls = 0

    async def fetch_page(self, query: str, page: int) -> ConnectorPage:
        self.fetch_calls += 1
        matches = [d for d in _DOCS if query.lower() in d["title"].lower()]
        return ConnectorPage(items=tuple(matches), has_next=False)


class _FailingConnector(BaseConnectorPlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id=PLUGIN)

    async def fetch_page(self, query: str, page: int) -> ConnectorPage:
        raise ConnectionError("source unavailable")


async def test_connector_search_returns_normalized_items() -> None:
    connector = _FakeConnector()

    result = await connector.search(_context(PlatformEventBus()), "Alpha")

    assert result.items == ({"id": "1", "title": "Alpha"},)
    assert result.warnings == ()


async def test_connector_search_uses_cache_on_second_call() -> None:
    connector = _FakeConnector()
    context = _context(PlatformEventBus())

    await connector.search(context, "Alpha")
    await connector.search(context, "Alpha")

    assert connector.fetch_calls == 1


async def test_connector_search_turns_errors_into_warnings() -> None:
    connector = _FailingConnector()

    result = await connector.search(_context(PlatformEventBus()), "Alpha")

    assert result.items == ()
    assert len(result.warnings) == 1
    assert "source unavailable" in result.warnings[0]


async def test_connector_invoke_adapts_payload() -> None:
    connector = _FakeConnector()

    result = await connector.invoke(_context(PlatformEventBus()), {"query": "Beta"})

    assert result["items"] == [{"id": "2", "title": "Beta"}]
