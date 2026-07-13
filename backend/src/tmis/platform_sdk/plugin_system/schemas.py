from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class PluginType(StrEnum):
    AGENT = "agent"
    CONNECTOR = "connector"
    WORKFLOW = "workflow"
    DOCUMENT_TEMPLATE = "document_template"
    TOOL = "tool"
    # Added in Sprint 24 — a Legal Copilot (tmis.legal_copilot_framework)
    # publishes as a plugin of this type, reusing install/update/
    # dependency/licensing here rather than a fourth marketplace layer.
    COPILOT = "copilot"


class PublishingStatus(StrEnum):
    """The lifecycle the sprint asks for: Développement → Validation →
    Signature → Publication → Retrait. "Installation"/"Mise à jour"
    are deliberately NOT statuses here — a plugin manifest is a single
    global catalog entry, but it can be installed by many cabinets
    independently (see `tmis.platform_sdk.extensions`), so per-firm
    installation state lives there, not on the manifest itself."""

    DEVELOPMENT = "development"
    VALIDATED = "validated"
    SIGNED = "signed"
    PUBLISHED = "published"
    RETIRED = "retired"


@dataclass(slots=True)
class PluginManifest:
    """The declarative identity of a plugin — the sprint's "PLUGIN
    SYSTEM" spec: identifiant, version, auteur, permissions,
    dépendances, signature, licence, description, compatibilité."""

    id: str
    name: str
    version: str
    plugin_type: PluginType
    author: str
    description: str
    license: str
    permissions: frozenset[str] = field(default_factory=frozenset)
    dependencies: tuple[str, ...] = ()
    compatibility: str = "*"
    signature: str | None = None
    status: PublishingStatus = PublishingStatus.DEVELOPMENT
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
