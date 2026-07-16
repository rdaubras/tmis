from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum

from tmis.ai_team.capabilities.schemas import LegalDomain


class CopilotStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


@dataclass(slots=True)
class LegalCopilot:
    """The assembled runtime object: a copilot is a `Team` id
    (`ai_team.teams.Team`, built via `TeamBuilder.build_custom_team`)
    plus a set of pack ids, each resolved through its own pack
    engine. This dataclass never embeds pack content — it only points
    at it, so a pack update is visible to every copilot referencing
    it without republishing the copilot itself."""

    id: str
    name: str
    domain: LegalDomain
    description: str
    version: str
    dependencies: tuple[str, ...]
    team_id: str
    compatible_models: frozenset[str]
    prompt_pack_id: str | None
    knowledge_pack_ids: tuple[str, ...]
    reasoning_pack_ids: tuple[str, ...]
    document_pack_ids: tuple[str, ...]
    workflow_pack_ids: tuple[str, ...]
    validation_policy_ids: tuple[str, ...]
    permissions: frozenset[str]
    metrics_enabled: bool = True
    status: CopilotStatus = CopilotStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class CopilotActivation:
    """A read-only view over the firm's `platform_sdk.extensions.
    ExtensionInstance` for this copilot — no longer its own stored
    record (see the Sprint 24 audit report for why per-copilot
    activation stayed separate from `business_platform.modules.
    TmisModule`, and docs/171-audit-marketplace.md §4 for why this
    stopped being a *second* record to keep in sync with that
    instance). `CopilotEngine.activate`/`.deactivate` write only
    through `ExtensionEngine`/`MarketplaceSubscriptionEngine`; this
    dataclass is reconstructed from the resulting instance on every
    read, never persisted itself."""

    firm_id: str
    copilot_id: str
    active: bool
    version: str
    granted_permissions: frozenset[str]
    updated_at: datetime
