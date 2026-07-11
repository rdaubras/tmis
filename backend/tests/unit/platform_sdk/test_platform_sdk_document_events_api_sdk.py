import pytest

from tmis.legal_drafting.templates.schemas import DocumentType
from tmis.platform_sdk.api_sdk.client import TmisApiClient
from tmis.platform_sdk.api_sdk.transports import InMemoryTransport
from tmis.platform_sdk.document_sdk.base import BaseDocumentTemplatePlugin, MissingVariablesError
from tmis.platform_sdk.document_sdk.schemas import (
    DocumentTemplateDefinition,
    TemplateSectionRef,
    TemplateVariable,
)
from tmis.platform_sdk.events_sdk.bus import PlatformEventBus
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.sdk.schemas import PluginContext

FIRM = "firm-a"

_DEFINITION = DocumentTemplateDefinition(
    id="tpl-1",
    name="Consultation",
    document_type=DocumentType.CONSULTATION,
    variables=(TemplateVariable("client_name", "Client"),),
    sections=(TemplateSectionRef("header", "Header", order=1),),
)


class _SimpleTemplate(BaseDocumentTemplatePlugin):
    def __init__(self) -> None:
        super().__init__(plugin_id="tpl-1", definition=_DEFINITION)

    def render_section(self, section_key: str, variables: dict) -> str:  # type: ignore[type-arg]
        return f"{section_key}:{variables['client_name']}"


def _context(events: PlatformEventBus) -> PluginContext:
    permissions = PermissionEngine(InMemoryPermissionStore())
    return PluginContext(
        firm_id=FIRM,
        actor_id="a",
        plugin_id="tpl-1",
        events=events,
        permissions=permissions.checker_for(FIRM, "tpl-1"),
    )


async def test_document_template_invoke_renders_sections() -> None:
    plugin = _SimpleTemplate()

    result = await plugin.invoke(
        _context(PlatformEventBus()), {"variables": {"client_name": "Exemplia"}}
    )

    assert result["sections"] == {"header": "header:Exemplia"}
    assert result["document_type"] == "consultation"


async def test_document_template_invoke_raises_on_missing_variable() -> None:
    plugin = _SimpleTemplate()

    with pytest.raises(MissingVariablesError):
        await plugin.invoke(_context(PlatformEventBus()), {"variables": {}})


async def test_document_template_publishes_draft_generated_event() -> None:
    events = PlatformEventBus()
    plugin = _SimpleTemplate()

    await plugin.invoke(_context(events), {"variables": {"client_name": "Exemplia"}})

    assert events.history[0].event_name == "DraftGenerated"


async def test_platform_event_bus_subscribe_and_publish() -> None:
    bus = PlatformEventBus()
    received = []

    async def handler(event) -> None:  # type: ignore[no-untyped-def]
        received.append(event.payload)

    bus.subscribe("DocumentUploaded", handler)
    await bus.publish("DocumentUploaded", {"document_id": "doc-1"})

    assert received == [{"document_id": "doc-1"}]
    assert len(bus.history) == 1


async def test_platform_event_bus_unsubscribe() -> None:
    bus = PlatformEventBus()
    calls = []

    async def handler(event) -> None:  # type: ignore[no-untyped-def]
        calls.append(event)

    bus.subscribe("TaskCompleted", handler)
    bus.unsubscribe("TaskCompleted", handler)
    await bus.publish("TaskCompleted", {})

    assert calls == []


async def test_api_client_uses_in_memory_transport() -> None:
    transport = InMemoryTransport()
    transport.stub("GET", "/api/v1/platform-sdk/marketplace", {"items": []})
    client = TmisApiClient(transport)

    result = await client.list_marketplace_plugins()

    assert result == {"items": []}
    assert transport.calls == [("GET", "/api/v1/platform-sdk/marketplace", None)]


async def test_api_client_install_plugin_posts_expected_body() -> None:
    transport = InMemoryTransport()
    transport.stub("POST", "/api/v1/platform-sdk/marketplace/agent-fiscal/install", {"id": "ext-1"})
    client = TmisApiClient(transport)

    result = await client.install_plugin("firm-demo", "agent-fiscal", ["read_cases"])

    assert result == {"id": "ext-1"}
    assert transport.calls[0][2] == {"firm_id": "firm-demo", "permissions": ["read_cases"]}
