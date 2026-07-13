from dataclasses import dataclass, field
from datetime import UTC, datetime

from tmis.ai_team.capabilities.schemas import LegalDomain


@dataclass(frozen=True, slots=True)
class PromptPack:
    """A named, versioned bundle of `ai.prompts.PromptRegistry` entries
    for one legal domain. `PromptRegistry` already versions individual
    prompts (Sprint 2) but has no bundle/inheritance concept — this is
    exactly that thin layer, storage/rendering still fully delegated
    to `PromptRegistry`. `overrides` maps a base `prompt_id` to the
    id of the prompt that should be used instead *for this pack* —
    both ids must already be registered in `PromptRegistry`; no prompt
    text is duplicated here."""

    id: str
    name: str
    domain: LegalDomain
    version: int
    system_prompt_ids: tuple[str, ...] = ()
    business_prompt_ids: tuple[str, ...] = ()
    parent_pack_id: str | None = None
    overrides: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
