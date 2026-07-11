import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from tmis.platform_sdk.permissions.schemas import ExtensionPermission


class ExtensionStatus(StrEnum):
    ACTIVE = "active"
    DISABLED = "disabled"
    UNINSTALLED = "uninstalled"


def new_extension_id() -> str:
    return f"ext-{uuid.uuid4()}"


@dataclass(slots=True)
class ExtensionInstance:
    """A plugin installed for one specific cabinet — distinct from
    `PluginManifest` (the global, single catalog entry a plugin author
    publishes once) the same way a Sprint 11 `Team` is distinct from
    an `AgentDescriptor`: many cabinets can install the same published
    plugin, each with its own granted permissions and lifecycle."""

    id: str
    firm_id: str
    plugin_id: str
    version: str
    granted_permissions: frozenset[ExtensionPermission]
    status: ExtensionStatus = ExtensionStatus.ACTIVE
    installed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
