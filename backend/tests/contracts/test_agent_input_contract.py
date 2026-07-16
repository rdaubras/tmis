"""Contract tests for `AgentInput`/`AgentOutput` (`tmis.ai.schemas.agent`),
the type crossing the boundary between every HTTP-facing endpoint and
every specialized agent (`tmis.agents.*`) and third-party plugin
(`tmis.platform_sdk.agent_sdk.base.BaseAgentPlugin`).

Unlike the per-module unit tests (`tests/unit/agents/test_*.py`), which
construct `AgentInput` by hand, this suite builds it from the most
upstream production entry point that turns a raw, untyped HTTP payload
into an `AgentInput` (`tmis.api.v1.chat.routes._agent_input`, fed with a
`ChatMessageRequest` the way FastAPI itself would deserialize one), then
drives it through every real, unmodified agent/consumer downstream —
including `BaseAgentPlugin.invoke()`, which the Sprint 43 audit found had
never been exercised with a realistic (non-UUID) `case_id` before the
Sprint 42 fix (see docs/reports/sprint-43-rapport-audit.md).

Regression-first: `test_a_pre_sprint42_style_uuid_parse_would_have_raised`
reproduces the exact construction `BaseAgentPlugin.invoke()` used before
Sprint 42 (`uuid.UUID(str(case_id))`) and asserts it *would* raise for a
free-form case id — proving the other tests in this module would have
failed before that fix, not just that they pass now.
"""

import uuid

import pytest

from tmis.agents.analysis_agent import AnalysisAgent
from tmis.agents.contract_agent import ContractAgent
from tmis.agents.jurisprudence_agent import JurisprudenceAgent
from tmis.agents.research_agent import ResearchAgent
from tmis.agents.synthesis_agent import SynthesisAgent
from tmis.agents.watch_agent import WatchAgent
from tmis.ai.schemas.agent import AgentInput, AgentOutput, ConfidenceLevel
from tmis.api.v1.chat.routes import _agent_input
from tmis.api.v1.chat.schemas import ChatMessageRequest
from tmis.case_intelligence.cases.in_memory_store import InMemoryCaseStore
from tmis.platform_sdk.agent_sdk.base import BaseAgentPlugin
from tmis.platform_sdk.events_sdk.bus import PlatformEventBus
from tmis.platform_sdk.permissions.engine import PermissionEngine
from tmis.platform_sdk.permissions.store import InMemoryPermissionStore
from tmis.platform_sdk.sdk.schemas import PluginContext

# A free-form, non-UUID case id — exactly the shape `CaseStorePort` accepts
# (see `case_intelligence.cases.ports.CaseStorePort.get`) and exactly the
# shape that broke `uuid.UUID(...)` parsing pre-Sprint-42.
_NON_UUID_CASE_ID = "case-contract-1"


def _raw_chat_payload() -> ChatMessageRequest:
    """The real production entry point: what FastAPI builds from a raw
    JSON body posted to `/api/v1/chat/stream`."""
    return ChatMessageRequest(
        conversation_id=uuid.uuid4(),
        message="Ou en est ce dossier ?",
        case_id=_NON_UUID_CASE_ID,
    )


def test_a_pre_sprint42_style_uuid_parse_would_have_raised() -> None:
    """Regression-first: prove the bug this suite guards against is real,
    not hypothetical — the exact expression `BaseAgentPlugin.invoke()`
    used before Sprint 42 raises for a realistic case id."""
    with pytest.raises(ValueError):
        uuid.UUID(str(_NON_UUID_CASE_ID))


def test_agent_input_built_from_the_chat_endpoint_carries_the_raw_case_id() -> None:
    agent_input = _agent_input(_raw_chat_payload())

    assert agent_input.case_id == _NON_UUID_CASE_ID
    assert isinstance(agent_input.case_id, str)


@pytest.mark.parametrize(
    "agent",
    [
        AnalysisAgent(),
        SynthesisAgent(),
        ContractAgent(),
        JurisprudenceAgent(),
        ResearchAgent(),
    ],
)
async def test_every_agent_consumes_a_chat_built_agent_input_without_raising(agent: object) -> None:
    """Every specialized agent must accept an `AgentInput` built exactly
    as the chat endpoint builds it (non-UUID `case_id` included) and
    return a well-formed `AgentOutput` — never raise."""
    case_store = InMemoryCaseStore()
    case_store.get_or_create(_NON_UUID_CASE_ID, title="Dossier contrat")
    agent._case_store = case_store  # type: ignore[attr-defined]  # noqa: SLF001

    payload = _raw_chat_payload()
    payload.message = "contrat de travail à durée indéterminée peut être rompu"
    agent_input = _agent_input(payload)

    output = await agent.run(agent_input)  # type: ignore[attr-defined]

    assert isinstance(output, AgentOutput)


async def test_watch_agent_consumes_a_chat_built_agent_input_without_raising() -> None:
    """`WatchAgent` has no `case_store` of its own (see
    docs/reports/sprint-43-rapport-audit.md) — it only ever reads
    `agent_input.case_id` to tag results, so it is exercised separately
    from the `case_store`-injected agents above."""
    agent = WatchAgent()
    payload = _raw_chat_payload()
    payload.message = "contrat de travail à durée indéterminée peut être rompu"

    output = await agent.run(_agent_input(payload))

    assert isinstance(output, AgentOutput)


class _ContractEchoPlugin(BaseAgentPlugin):
    """A minimal, self-contained `BaseAgentPlugin` — deliberately not
    reused from `tests/unit/platform_sdk/test_platform_sdk_agent_connector_sdk.py`,
    since this suite must stay independent of per-module unit tests."""

    def __init__(self) -> None:
        super().__init__(plugin_id="contract-echo")

    @property
    def capabilities(self) -> tuple[str, ...]:
        return ("echo",)

    async def run(self, context: PluginContext, agent_input: AgentInput) -> AgentOutput:
        return AgentOutput(
            result={"case_id": agent_input.case_id},
            confidence=ConfidenceLevel.HIGH,
        )


def _plugin_context() -> PluginContext:
    permissions = PermissionEngine(InMemoryPermissionStore())
    return PluginContext(
        firm_id="firm-contract",
        actor_id="avocat-contract",
        plugin_id="contract-echo",
        events=PlatformEventBus(),
        permissions=permissions.checker_for("firm-contract", "contract-echo"),
    )


async def test_base_agent_plugin_invoke_accepts_the_same_non_uuid_case_id_a_client_would_send() -> (
    None
):
    """The consumer the Sprint 43 audit flagged as previously unexercised
    with a realistic case id: a raw plugin payload dict (as a third-party
    plugin's caller would build it, not an `AgentInput`) carrying the same
    non-UUID `case_id` a chat client sends. Before Sprint 42 this raised
    `ValueError` inside `invoke()`, silently breaking every plugin
    (`AgentFiscalPlugin`, `AgentDroitSocialPlugin`, ...) for any firm using
    non-UUID case ids."""
    plugin = _ContractEchoPlugin()

    result = await plugin.invoke(_plugin_context(), {"case_id": _NON_UUID_CASE_ID})

    assert result["result"]["case_id"] == _NON_UUID_CASE_ID
