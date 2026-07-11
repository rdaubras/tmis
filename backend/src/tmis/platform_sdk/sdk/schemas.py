from dataclasses import dataclass, field
from typing import Any

from tmis.ai_team.agents.ports import KernelPort
from tmis.platform_sdk.sdk.ports import EventPublisherPort, PermissionCheckerPort


@dataclass(frozen=True, slots=True)
class PluginContext:
    """Injected into every plugin invocation — the sprint's "Agent
    SDK" spec ("recevoir un contexte") generalized to every plugin
    type. A plugin only ever reaches the rest of TMIS through the
    three narrow ports carried here — never by importing a bounded
    context module directly — so `tmis.platform_sdk.sandbox` remains
    the single chokepoint that can audit and gate every call."""

    firm_id: str
    actor_id: str
    plugin_id: str
    events: EventPublisherPort
    permissions: PermissionCheckerPort
    kernel: KernelPort | None = None
    config: dict[str, Any] = field(default_factory=dict)
