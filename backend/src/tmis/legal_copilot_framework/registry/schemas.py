from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.ai_team.capabilities.schemas import LegalDomain
from tmis.legal_copilot_framework.copilot.schemas import CopilotStatus


@dataclass(slots=True)
class CopilotManifest:
    """One catalog entry — the Phase 4 "Copilot Registry" the sprint
    asks for: id, version, domain, author, status, dependencies,
    history, compatibility. Kept separate from `copilot.LegalCopilot`
    (the assembled runtime object) on purpose: the registry tracks
    *publishing* metadata across every version ever registered, the
    same "keep full history, never overwrite" convention already used
    by `ai.prompts.PromptRegistry` and `legal_drafting.templates.
    TemplateRegistry`."""

    copilot_id: str
    version: str
    domain: LegalDomain
    author: str
    status: CopilotStatus
    dependencies: tuple[str, ...] = ()
    compatibility: str = "*"
    license: str = "proprietary"
    """Same free-form vocabulary as `platform_sdk.plugin_system.
    PluginManifest.license` (a plain string, e.g. "MIT" or
    "proprietary") — replaces the `_LICENSE` constant that used to be
    hard-coded in `copilot.marketplace.to_plugin_manifest`, one
    licence per copilot version rather than one for every copilot
    ever published."""
    published_at: datetime = field(default_factory=lambda: datetime.now(UTC))
