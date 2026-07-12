from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class TmisModule(StrEnum):
    """The TMIS bounded contexts that can be independently enabled or
    disabled per firm. A module is gated by plan feature (see
    `plans.schemas.Plan.features`, using the same string value as
    this enum's member) and may additionally be explicitly toggled
    per firm via `ModuleActivation` — see `ModuleRegistry`."""

    DOCUMENT_INTELLIGENCE = "document_intelligence"
    CASE_INTELLIGENCE = "case_intelligence"
    LEGAL_RESEARCH = "legal_research"
    LEGAL_REASONING = "legal_reasoning"
    LEGAL_DRAFTING = "legal_drafting"
    COLLABORATION = "collaboration"
    CABINET_OS = "cabinet_os"
    AI_TEAM = "ai_team"
    CABINET_KNOWLEDGE = "cabinet_knowledge"
    PLATFORM_SDK = "platform_sdk"
    AI_FABRIC = "ai_fabric"
    AI_GOVERNANCE = "ai_governance"
    STRATEGIC_INTELLIGENCE = "strategic_intelligence"
    WORKFLOW_AUTOMATION = "workflow_automation"
    INTEGRATION_HUB = "integration_hub"
    IDENTITY_PLATFORM = "identity_platform"


@dataclass(slots=True)
class ModuleActivation:
    """An explicit per-firm override of a module's default
    availability. Absence of a record means the module follows its
    plan-derived default (available if the plan's features include
    the module's value) — see `ModuleRegistry.is_active`."""

    firm_id: str
    module: TmisModule
    active: bool
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
