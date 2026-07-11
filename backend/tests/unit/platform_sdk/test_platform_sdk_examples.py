import uuid

from tmis.ai.schemas.agent import AgentInput
from tmis.platform_sdk.events_sdk.bus import PlatformEventBus
from tmis.platform_sdk.examples.agent_droit_social import AgentDroitSocialPlugin
from tmis.platform_sdk.examples.agent_fiscal import AgentFiscalPlugin
from tmis.platform_sdk.examples.document_template_consultation import (
    DocumentTemplateConsultationPlugin,
)
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.sdk.schemas import PluginContext

FIRM = "firm-a"


def _context(plugin_id: str) -> PluginContext:
    permissions = PermissionEngine(InMemoryPermissionStore())
    return PluginContext(
        firm_id=FIRM,
        actor_id="avocat1",
        plugin_id=plugin_id,
        events=PlatformEventBus(),
        permissions=permissions.checker_for(FIRM, plugin_id),
    )


async def test_agent_fiscal_without_kernel_uses_fallback_text() -> None:
    agent = AgentFiscalPlugin()
    assert agent.capabilities == ("fiscal_analysis",)

    output = await agent.run(
        _context(agent.id),
        AgentInput(task_id=uuid.uuid4(), case_id=None, context={"question": "TVA ?"}),
    )

    assert "TVA" in str(output.result["text"])
    assert output.result["agent_role"] == "fiscal_expert"


async def test_agent_droit_social_without_kernel_uses_fallback_text() -> None:
    agent = AgentDroitSocialPlugin()
    assert agent.capabilities == ("social_law_analysis",)

    output = await agent.run(
        _context(agent.id),
        AgentInput(task_id=uuid.uuid4(), case_id=None, context={"question": "Licenciement ?"}),
    )

    assert "Licenciement" in str(output.result["text"])
    assert output.result["agent_role"] == "social_law_expert"


def test_document_template_consultation_renders_every_section() -> None:
    plugin = DocumentTemplateConsultationPlugin()
    variables = {"client_name": "Exemplia", "question": "Délai de prescription ?"}

    assert plugin.render_section("header", variables) == "Consultation juridique — Exemplia"
    assert plugin.render_section("question", variables) == (
        "Question posée : Délai de prescription ?"
    )
    assert plugin.render_section("analysis", variables) == "Analyse à compléter."
    assert plugin.render_section("analysis", {**variables, "recommandation": "Agir vite"}) == (
        "Agir vite"
    )
    assert plugin.render_section("unknown", variables) == ""


async def test_document_template_consultation_invoke_end_to_end() -> None:
    plugin = DocumentTemplateConsultationPlugin()

    result = await plugin.invoke(
        _context(plugin.id),
        {"variables": {"client_name": "Exemplia", "question": "Délai ?"}},
    )

    assert result["sections"]["header"] == "Consultation juridique — Exemplia"
    assert result["document_type"] == "consultation"
